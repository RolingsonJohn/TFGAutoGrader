from statistics import StatisticsError, mean, mode
from pydantic import BaseModel
from services.Evaluation.LLMClient import LLMClient
from threading import Lock, get_ident
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from ollama import Client
from services.Config import Config as config
import os
import re
import time

mutex = Lock()

class StudentsInfo(BaseModel):
    """ 
    Esquema de salida de la respuesta del modelo LLM
    a la solicitud realizada
    """
    name: str
    grade: float
    error_feedback: str

class Evaluator:

    """
        Clase que instancia a un cliente LLM y se encarga de estructurar la solicitud
        de evaluación
    """

    def __init__(self, codes: dict = {}, rubrics: dict = {}, max_threads: int = 3, exe_mode: str = config.EXE_METHOD,
                 system_template:str = "", prompt_template: str = "", language: str = "c", model :str = config.OLLAMA_MODEL):
        """
            Método de inicialización de la clase
            Input:
                - codes (dict): Diccionario con clave = nombre del fichero y valor = código a evaluar.
                - rubrics (dict): Diccionario con clave = nombre del aspecto de la rúbrica y valor = Criterio y peso de la rúbrica.
                - max_threads (int): Máximo número de hilos a instanciar para el número de evaluadores.
                - exe_mode (str): Indica que tipo de agente LLM se va a emplear (ollama, groq, google).
                - system_template (str): Plantilla de configuración del modelo para dotarlo de un contexto.
                - prompt_template (str): Plantilla del prompt a solicitar al modelo.
                - language (str): Lenguaje de programación en el que está escrito el programa a evaluar.
                - model (str): Modelo de LLM que se utilizará para la evaluación del código.
        """
        self.client = LLMClient(exe_mode=exe_mode, system_context=system_template, model=model)
        self.exe_mode = exe_mode
        self.codes = codes
        self.structure = StudentsInfo
        self.results = []
        self.rubrics = rubrics
        self.max_threads = max_threads
        self.language = language
        self.format = "Json"
        self.system_template = system_template
        self.prompt_template = prompt_template


    def zero_shot_prompt(self, filename: str, code: str, client: LLMClient) -> dict:

        """
            Método de prompting donde se le solicita al modelo evaluar un código solo
            otorgando la rúbrica de corrección y el código a evaluar.

            Input:
                - filename (str): Nombre del fichero donde se encuentra el código.
                - code (str): Código a evaluar.
                - client (LLMClient): Cliente LLM que se encarga de la evaluación del ejercicio.
            Output:
                - StudentInfo: Calificación y retroalimentación del código evaluado.
        """
        
        prompt = re.sub("<CODE>", code, self.prompt_template)
        data = prompt
        for key, rubric in self.rubrics.items():
            if key != 'Code':
                criterios = rubric.get("criteria")
                criteria = f'## Criteria {key}\n'
                for criterio in criterios:
                    criteria += f'- {criterio}\n'
                criteria += f'### Weight = {rubric.get("weight")}'
            
                data = re.sub("<ASPECT>", key, data)
            data = re.sub("<RUBRIC>", criteria, data)
            data += '\n<RUBRIC>'
        data = re.sub("<RUBRIC>", "", data)

        # print(f"Hilo Evaluando: {get_ident()}\nPrompt:\n{data}\n\n")

        with mutex:
            response = client.chat(structure=StudentsInfo, prompt=data)
            if self.exe_mode != 'ollama':
                time.sleep(5)

        response_refine = self.deep_thinking(client, filename, code, response.get('grade'), 10.0, response.get('error_feedback'))
        try:
            response.update({"refine_grade": response_refine.get("grade")})
            response.update({"refine_feedback": response_refine.get("feedback")})
        except Exception as e:
            response.update({"refine_grade":0})
            response.update({"refine_feedback": 'NULL'})

        response.update({"name" : filename})

        print(response)
        return response
    

    def few_shots_prompt(self, filename: str, code: str, client: LLMClient) -> dict:

        """
            Método de prompting donde se le solicita al modelo evaluar un código,
            otorgando la rúbrica de corrección, el código a evaluar y una serie de ejemplos
            que le sirvan de contexto para una corrección más precisa.

            Input:
                - filename (str): Nombre del fichero donde se encuentra el código.
                - code (str): Código a evaluar.
                - client (LLMClient): Cliente LLM que se encarga de la evaluación del ejercicio.
            Output:
                - StudentInfo: Calificación y retroalimentación del código evaluado.
        """
        
        prompt = re.sub("<CODE>", code, self.prompt_template)
        data = prompt
        for key, rubric in self.rubrics.items():
            if key != 'Code':
                criterios = rubric.get("criteria")
                criteria = f'## Criteria {key}\n'
                for criterio in criterios:
                    criteria += f'- {criterio}\n'
                criteria += f'### Weight = {rubric.get("weight")}'
            
            else:
                rubric = f"This is an example of a code grading with a 10\n{rubric}"
                data = re.sub("<RUBRIC>", rubric, data)
                
            data = re.sub("<RUBRIC>", criteria, data)
            data += '\n<RUBRIC>'
        data = re.sub("<RUBRIC>", "", data)

        print(f"Hilo Evaluando: {get_ident()}\nPrompt:\n{data}\n\n")

        with mutex:
            response = client.chat(structure=StudentsInfo, prompt=data)
            if self.exe_mode != 'ollama':
                time.sleep(5)

        response_refine = self.deep_thinking(client, filename, code, response.get('grade'), 10.0, response.get('error_feedback'))
        try:
            response.update({"refine_grade": response_refine.get("grade")})
            response.update({"refine_feedback": response_refine.get("feedback")})
        except Exception as e:
            response.update({"refine_grade":0})
            response.update({"refine_feedback": 'NULL'})

        response.update({"name" : filename})
        return response


    def cot_prompt(self, filename: str, code: str, client: LLMClient)-> dict:

        """
        Método de prompting donde se le solicita al modelo evaluar un código,
        otorgando la rúbrica de corrección, el código a evaluar, una serie de ejemplos
        que le sirvan de contexto para una corrección más precisa y dividiendo los aspectos
        de la rúbrica, para procesarlos paso a paso.

        Input:
            - filename (str): Nombre del fichero donde se encuentra el código.
            - code (str): Código a evaluar.
            - client (LLMClient): Cliente LLM que se encarga de la evaluación del ejercicio.
        Output:
            - StudentInfo: Calificación y retroalimentación del código evaluado.
        """
        
        #prompt, system_config = self.replace_tags(code, self.prompt_template, self.system_template)
        prompt = re.sub("<CODE>", code, self.prompt_template)
        feedbacks = {}
        grades = []
        rubric_grade = {}
        for key, rubric in self.rubrics.items():
            if key != 'Code':
                criterios = rubric.get("criteria")
                criteria = f'## Criteria {key}\n'
                for criterio in criterios:
                    criteria += f'- {criterio}\n'
                criteria += f'### Weight = {rubric.get("weight")}'
                data = re.sub("<RUBRIC>", criteria, prompt)
                data = re.sub("<ASPECT>", key, data)
                data += "\n**MAKE SURE THAT THE NOTE YOU ASSIGNED RESPECT THE WEIGHT CRITERIA**"

                data += f"\nThis is an example of a code grading with a 10\n{self.rubrics.get("Code")}"
                
                with mutex:
                    response = client.chat(structure=StudentsInfo, prompt=data)
                    if self.exe_mode != 'ollama':
                        time.sleep(1)

                # response = self.deep_thinking(client, filename, code, response.get("grade"), {rubric.get("weight")}, response.get("error_feedback"))
                rubric_grade.update({key:response.get("grade")})
                feedback = response.get("error_feedback")
                grades.append(response.get("grade"))

                feedbacks.update({key : feedback})
                prompt += f"\n# Feedback for {key}\n{feedback}"
                # prompt += f"\n## Grade for {key} = {response.get("grade")}/{rubric.get("weight")}"

                print(f"Hilo Evaluando: {get_ident()}\nPrompt = \n{data}\n\n")
        print(f"Fichero {filename}, notas = {grades}")
        
        #final_grade = sum(grades) / len(grades) if grades else 0.0
        
        final_grade = sum(grades)
        response.update({"grade" : final_grade})
        response_refine = self.deep_thinking(client, filename, code, response.get('grade'), 10.0, response.get('error_feedback'))
        try:
            response.update({"refine_grade": response_refine.get("grade")})
            response.update({"refine_feedback": response_refine.get("feedback")})
        except Exception as e:
            response.update({"refine_grade":0})
            response.update({"refine_feedback": 'NULL'})

        response.update({"name" : filename})
        response.update({"grade" : final_grade})
        response.update({"error_feedback" : feedbacks})

        return response
    
    def deep_thinking(self, client: LLMClient, filename: str, code: str, prev_grade: float, weight: float, prev_feedback: str):
        """
        Estrategia que permite al modelo evaluar la primera respuesta que haya dado 
        a la evaluación. Mejorando de esta forma la precisión.

        Input:
            - client (LLMClient): Cliente LLM que se encarga de la evaluación del ejercicio.
            - filename (str): Nombre del fichero donde se encuentra el código.
            - code (str): Código a evaluar.
            - prev_grade (float): Nota asignada en la evaluación anterior.
            - weight (float): Peso de la calificación previa sobre el total del aspecto.
            - prev_feedback (str): Feedback asignado en la evaluación anterior.  
        Output:
            - StudentInfo: Calificación y retroalimentación del código evaluado.
        """

        prompt = f"""
    Tu tarea es revisar una evaluación automática anterior hecha a un fragmento de código en {self.language}. 
    El objetivo es detectar si la calificación fue justa y si la retroalimentación puede mejorarse.

    ### Código del estudiante:
    {code}

    ### Evaluación previa:
    - Nota: {prev_grade}/{weight}
    - Feedback: {prev_feedback}

    ### Instrucciones:
    1. Evalúa si la nota anterior es coherente con el código y la rúbrica.
    2. Justifica cualquier corrección que propongas.
    3. Da una nueva calificación solo si es necesario.
    4. Devuelve la salida en formato JSON:
        """.strip()

        print(f"[Deep Thinking] Revisión del archivo {filename} con prompt:\n{prompt}\n")

        with mutex:
            response = client.chat(structure=StudentsInfo, prompt=prompt)

        print(f"Reevaluación {response.get("grade")}")
        response.update({"name": filename})
        return response

    
    def launch_threads(self, method) -> list[dict]:
        """
        Método que permite realizar las evaluaciones de los códigos de manera concurrente.
        Input:
            - method: Método de evaluación que se empleará para la evaluación por votación.
        Output:
            - list[StudentInfo]: Listado de todas las calificaciones y feedbacks de todos los ejercicios a evaluar.
        """
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(method, filename, code, self.client): (filename, code) for filename, code in self.codes.items()}
            for future in as_completed(futures):
                result = future.result()
                self.results.append({
                    "name": result.get("name"),
                    "grade": result.get("grade"),
                    "refine_grade": result.get("refine_grade"),
                    "error_feedback": result.get("error_feedback"),
                    "refine_feedback": result.get("refine_feedback"),
                })
        return self.results


    def grade_by_voting(self, method, clients: list[LLMClient]) -> list[dict]:
        """
        Método de evaluación por votación donde se instancian max_threads clientes, con el fin
        de obtener una calificación lo más justa posible.

        Input:
            - method: Método de evaluación que se empleará para la evaluación por votación.
            - clients: Lista de clientes que se utilizarán para la evaluación.
        Output:
            - list[StudentInfo]: Listado de todas las calificaciones y feedbacks de todos los ejercicios a evaluar.
        """
        final_results = []

        print(self.client.model)
        for filename, code in self.codes.items():
            grades = []
            ref_grades = []
            feedbacks = []
            refine_feedbacks = []

            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = [executor.submit(method, filename, code, client) for client in clients]
                for future in as_completed(futures):
                    result = future.result()
                    grades.append(round(result.get("grade", 0), 2))
                    ref_grades.append(round(result.get("refine_grade", 0), 2))
                    feedbacks.append(result.get("error_feedback", ""))
                    refine_feedbacks.append(result.get("refine_feedbacks", ""))

            try:
                # Intentar moda
                final_grade = mode(grades)
                refine_grade = mode(ref_grades)
            except StatisticsError:
                # No hay moda clara, calcular media
                final_grade = round(mean(grades), 2)
                refine_grade = round(mean(grades), 2)

            # Combinar feedbacks únicos si es posible
            combined_feedback = "\n---\n".join(set(str(fb) for fb in feedbacks))

            final_results.append({
                "name": filename,
                "grade": final_grade,
                "refine_grade": refine_grade,
                "error_feedback": combined_feedback,
                "refine_feedback": refine_feedbacks,
            })

        return final_results