import re
import json
import groq
from pydantic import BaseModel
from ollama import Client
import google.generativeai as genai
from services.Config import Config as config
from google.generativeai.types import GenerationConfig

class NonSuportedMode(Exception):
    """
        Excepción en caso de no utilizar
        un modelo soportado por la app.
    """
    def __init__(self, *args):
        super().__init__(*args)

class LLMClient:

    """
        Clase encargada de albergar la interacción con las APIs de
        los LLM.
    """

    def __init__(self, exe_mode: str = config.EXE_METHOD, 
                 system_context: str = "",
                 model: str = config.OLLAMA_MODEL):
        """
            Método de inicialización de la clase
            Input:
                - exe_mode (str): Indica que tipo de agente LLM se va a emplear (ollama, groq, google).
                - systema_context (str): Plantilla de configuración del modelo para dotarlo de un contexto.
                - model (str): Modelo de LLM que se utilizará para la evaluación del código.
        """
        
        self.exe_mode = exe_mode
        self.system_context = system_context

        match self.exe_mode:
            case "google":
                self.model = model
                genai.configure(api_key=config.API_KEY_GOOGLE)
                self.client = genai.GenerativeModel(self.model, system_instruction=self.system_context)
            case "ollama":
                self.model = model
                self.client = None
            case "groq":
                self.model = model
                self.client = groq.Groq(api_key=config.API_KEY_GROQ)
            case _:
                raise NonSuportedMode("Execution mode non suported")

    def chat(self, structure: BaseModel, prompt: str) -> dict:
        """
            Método encargado de la solicitud al LLM.
            Inputs:
                - structure (BaseModel): Esquema que seguirá la respuesta dada por el LLM.
                - prompt (str): Texto en leguaje natural empleado para la solicitud al modelo.
            Output:
                - Respuesta dada por el modelo con la estructura especificada por el parámetro structure.
        """
        try:
            match self.exe_mode:
                case "google":
                    
                    schema = json.dumps(structure.model_json_schema())

                    prompt = f"""{prompt}

The response must follow the JSON schema bellow:
```json
{schema}
```
"""
                    generation_config = GenerationConfig(
                        temperature=0.0
                    )

                    response = self.client.generate_content(
                        contents=[prompt],
                        generation_config=generation_config,
                    )
                    
                    response = re.sub(r"```(?:json)?\n?", "", response.text).strip()
                    response = re.sub(r"\n?```", "", response).strip()
                    response = structure.model_validate_json(response).model_dump()

                case "ollama":
                    print("Evaluando en el cliente")
                    self.client = Client()
                    response = self.client.chat(
                        model=self.model,
                        messages=[
                            {'role': 'system', 'content': self.system_context},
                            {'role': 'user', 'content': prompt}
                        ],
                        format=structure.model_json_schema(),
                        options={'temperature': 0},
                    )

                    response = structure.model_validate_json(response.message.content).model_dump()

                case "groq":

                    schema = json.dumps(structure.model_json_schema())

                    prompt = f"""{prompt}

The response must follow the JSON schema bellow:
```json
{schema}
```
"""
                    chat_completion = self.client.chat.completions.create(
                        messages=[
                            {
                                'role': 'system',
                                'content': self.system_context
                            },
                            {
                                'role': "user",
                                'content': prompt,
                            }
                        ],
                        model="llama-3.3-70b-versatile",
                        response_format={"type": "json_object"},
                        temperature=0.0
                    )

                    content = chat_completion.choices[0].message.content
                    content = re.sub(r"```(?:json)?\n?", "", content).strip()
                    content = re.sub(r"\n?```", "", content).strip()

                    response = structure.model_validate_json(content).model_dump()
                    print(f"------------------------\n{response}\n-----------------------")

                case _:
                    raise NonSuportedMode("Execution mode non suported during chat")
                
        except Exception as e:
            print(f"LLM error {e}")
            return None

        return response