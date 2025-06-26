from transformers import AutoTokenizer, AutoModel
from services.Config import Config as config
import torch
import chromadb
import numpy as np
import re
from chromadb.utils import embedding_functions


class Rag:
    """ 
    Módulo encargado de la gestión de la base de datos vectorial,
    usada para el almacenamiento de los códigos de ejemplo.
    """
    
    def __init__(self, tokenizer=config.TOKENIZER, collection_name: str = "", 
                 model=config.RAG_MODEL, chroma_path=""):
        """
            Método de inicialización de la clase
            Input:
                - tokenizer (str): Nombre del transformer utilizado para la tokenización del texto.
                - collection_name (str): Nombre de la colección donde se almacenan los ejemplos.
                - model (str): Nombre del modelo de transformer usado para el embedding del texto.
                - chroma_path (str): Ubicación de la base de datos vectorial.
        """
        
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer)
        self.model = AutoModel.from_pretrained(model)
        self.model.eval()

        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=re.sub(' ', '-', collection_name),
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model)
        )


    def get_embeddings(self, text: str) -> np.ndarray:
        """
        Método que permite obtener la representación
        vectorial del texto a almacenar en el RAG.
        Input:
            - text (str): Texto a almacenar.
        """

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)

        cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
        return cls_embedding
    

    def add_example(self, title: str, description: str, code: str, theme: list):
        """
            Método que permite añadir un ejemplo de código funcional
            Input:
                - title: Nombre del ejemplo
                - description: Breve descripción de como soluciona el problema
                - code: Código del ejemplo.
                - theme: Tema del problema a tratar.
        """
        title = re.sub(r'\s+', '-', title)  # Reemplaza espacios por guiones
        theme_str = ', '.join(theme)  # Convierte la lista en string separado por comas
        text = f"{title}\n{description}\n{code}"
        
        self.collection.add(
            documents=[text],
            ids=[title],
            metadatas=[{
                "title": title,
                "description": description,
                "theme": theme_str
            }],
            embeddings=self.get_embeddings(code)
        )


    def delete_example(self, title: str):
        """
            Método que permite eliminar un ejemplo concreto
            a partir del titulo de este.
            Input:
                - title (str): Titulo del ejemplo a eliminar
        """
        self.collection.delete(ids=[title])


    def delete_collection(self, name: str):
        """
            Método que permite eliminar una colección del RAG.
            Input:
                - name (str): nombre de la colección a eliminar
        """
        self.client.delete_collection(name=name)


    def get_examples(self, query: str, relatives: int = 3):
        """
            Método que permite extraer los ejemplos del RAG a partir
            de una query.
            Input:
                - query (str): Texto relacionado con el ejemplo.
                - relatives (int): Numero de ejemplos que coincidan con el embedding a extraer.
        """
        query = re.sub(' ', '', query)
        resultados = self.collection.query(
            query_texts=[query],
            n_results=relatives
        )
        return resultados