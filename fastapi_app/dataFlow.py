import seaborn as sns
import pandas as pd
import numpy as np
import ollama
from services.Evaluation import Evaluator as ev, LLMClient as cl, RubricGenerator as rub, Rag as rg
from services.PreEvaluation import FileLoader as fl
from pathlib import Path
from datetime import datetime
from services.Config.Config import EXE_METHOD, OLLAMA_MODEL, GROQ_MODEL, GENAI_MODEL
import time

def load_files(files: dict) -> dict:
    """
        Método encargado de la carga de datos
        Input:
            - file: Ficheros a cargar especificando ubicación y nombre.
        Output:
            - Datos a evaluar especificando contenido y nombre
    """
    codes = {}
    for file in files.values():
        codes.update({file : fl.FileLoader.load_files(file)})
    return codes


def run_evaluation(codes, exe_mode, model, rubric, system_config, prompt_template, repetitions=5):
    """
        Método encargado de lanzar n evaluaciones para estimar los resultados de estas.
    """
    all_results = []
    models = ollama.list()

    clients = []
    for _ in models.models:
        model_name = _.model
        print(model_name)
        clients.append(cl.LLMClient(
            exe_mode="ollama",
            system_context=system_config,
            model=model_name,
        ))

    print(f"{models.models}\n{clients}")
    for i in range(repetitions):
        print(f"\n[Repetición {i+1}/{repetitions}]\n{'-'*40}")
        evaluator = ev.Evaluator(
            codes=codes,
            rubrics=rubric,
            system_template=system_config,
            prompt_template=prompt_template,
            language='python',
            exe_mode=exe_mode,
            model=model,
            max_threads=1,
        )
        results = evaluator.grade_by_voting(evaluator.few_shots_prompt, clients)
        for res in results:
            all_results.append({
                "filename": res.get("name"),
                "grade": res.get("grade"),
                "refine_grade" : res.get("refine_grade"),
                "feedback" : res.get("error_feedback"),
                "refine_feedback" : res.get("refine_feedback"), 
                "run": i + 1,
                "model": model
            })

            print(res)

    df = pd.DataFrame(all_results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df.to_csv(f"{timestamp}_Calificaciones_{model}.csv", index=False)

    return all_results

def test_fib():
    BASE_DIR = Path(__file__).resolve().parent
    
    print("INICIO DE LA PRUEBA:")
    # Carga de ficheros
    files = fl.FileLoader.load_files_from_dir("test/Fibonacci")
    #codes = load_files({"test/Fibonacci" : "test/Fibonacci/formula.c"})
    codes = load_files(files)

    rag = rg.Rag(collection_name="Fibonacci Sequence", chroma_path=f"{BASE_DIR}/resources")
    
    rag.add_example(title="example", code=list(codes.values())[0], theme=["Fibonacci Sequence"], description="Sucesión de fibonacci")

    print(rag.get_examples("Sucesión de Fibonacci", relatives=1))

    # Templates
    tags = {"<PLANGUAGE>" : "c", "<FORMAT>" : "Json"}
    system_config = fl.FileLoader.replace_tags(
        template=fl.FileLoader.load_files(path=f"{BASE_DIR}/services/resources/system_template.dat"), tags=tags)
    prompt_template = fl.FileLoader.replace_tags(
        template=fl.FileLoader.load_files(path=f"{BASE_DIR}/services/resources/prompt_template.dat"), tags=tags)

    # Rúbricas
    rubric_gen = rub.RubricGenerator(system_config=system_config)
    rubric = rubric_gen.get_rubric("Fibonacci Sequence")

    # Ejecutar evaluaciones múltiples
    print("Evaluaciones con Ollama:")
    # all_results = run_evaluation(codes, "google", GENAI_MODEL, rubric, system_config, prompt_template, repetitions=5)
    # print("Evaluaciones con Groq:")
    models = ollama.list()

    for _ in models.models:
        all_results = run_evaluation(codes, "ollama", _.model, rubric, system_config, prompt_template, repetitions=5)
    # Visualización
    print("Evaluación finalizada")

def main():
    test_fib()

if __name__ == '__main__':
    main()
