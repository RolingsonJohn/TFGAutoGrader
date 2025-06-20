import os
import re
import json
import ollama
from pathlib import Path
from services.Config import Config as config
from pydantic import BaseModel
from services.Evaluation.LLMClient import LLMClient
from services.PreEvaluation.FileLoader import FileLoader
from typing import List

class Dimension(BaseModel):
	criteria: List[str]
	weight: float


class RubricFormat(BaseModel):
    Functionality: Dimension
    Quality: Dimension
    Efficiency: Dimension
    Logic: Dimension
    Code: str


class RubricGenerator:

    def __init__(self, system_config: str = "", exe_mode: str = config.EXE_METHOD):
        self.client = LLMClient(exe_mode=exe_mode, system_context=system_config)
        self.rubric_path = f"{Path(__file__).parent.parent}/resources/rubrics.json"


    def get_rubric(self, theme: str) -> dict:
        
        if os.path.exists(f"{Path(__file__).parent.parent}/resources/rubrics.json"):
            rubrics = self.load_rubrics()
        else:
            rubrics = self.generate_rubrics(theme= theme)

        return rubrics
    

    def load_rubrics(self) -> dict:

        with open(self.rubric_path, 'r', encoding='utf-8') as file:
            rubric = json.load(file)
        return rubric


    def generate_rubrics(self, theme: str) -> dict:

        prompt = FileLoader.load_files(f"{Path(__file__).parent.parent}/resources/rubric_template.dat")
        prompt = re.sub("<THEME>", theme, prompt)
        response = self.client.chat(structure=RubricFormat, prompt=prompt) 

        print(response)
        with open(self.rubric_path, 'w', encoding='utf-8') as file:
            json.dump(response, file, ensure_ascii=False, indent=4)

        return response
