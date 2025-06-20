import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import ollama
from services.Evaluation import Evaluator as ev, LLMClient as cl, RubricGenerator as rub, Rag as rg
from services.PreEvaluation import FileLoader as fl
from pathlib import Path
from datetime import datetime
from scipy.stats import pearsonr
from sklearn.metrics import (
    accuracy_score, cohen_kappa_score,
    mean_squared_error, mean_absolute_error
)
from services.Config.Config import EXE_METHOD, OLLAMA_MODEL, GROQ_MODEL, GENAI_MODEL
import time

def load_files(files: dict) -> dict:
    codes = {}
    for file in files.values():
        codes.update({file : fl.FileLoader.load_files(file)})
    return codes


def run_evaluation(codes, exe_mode, model, rubric, system_config, prompt_template, repetitions=5):
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


def plot_variation(data, name):
    df = pd.DataFrame(data)

    plt.figure(figsize=(12, 7))
    sns.boxplot(data=df, x="filename", y="grade", hue="model")
    sns.swarmplot(data=df, x="filename", y="grade", hue="model", 
                  dodge=True, palette="dark:.3", alpha=0.7, size=4)

    plt.title("Variación de notas por fichero y modelo")
    plt.ylabel("Nota")
    plt.xlabel("Fichero")
    plt.xticks(rotation=45)
    plt.legend(title="Modelo", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plt.savefig(f"{Path(__file__).resolve().parent}/outputs/{timestamp}_{name}.png")
    plt.close()


def plot_variations(results, expected_grades: dict, name: str):
    """
    Traza en un único gráfico:
      - grade         (círculos azules)
      - refine_grade  (diamantes morados)
      - expected_grade (cruces naranjas)

    results: lista de dicts con keys "filename", "grade", "refine_grade", "run", "model"
    expected_grades: dict { filename: expected_grade }
    name: sufijo para el archivo de salida (sin timestamp)
    """

    # 1) Creamos DataFrame con resultados y convertimos a float
    df = pd.DataFrame(results)
    df["grade"] = pd.to_numeric(df["grade"], errors="coerce")
    df["refine_grade"] = pd.to_numeric(df["refine_grade"], errors="coerce")
    
    # 2) Construimos un DataFrame para expected_grade (una fila por cada filename)
    df_expected = pd.DataFrame({
        "filename": df["filename"].unique()
    })
    df_expected["expected_grade"] = df_expected["filename"].map(expected_grades).astype(float)

    # 3) Montamos la figura
    plt.figure(figsize=(12, 7))

    # (a) Dibujamos 'grade' en azul como círculos
    sns.scatterplot(
        data=df,
        x="filename",
        y="grade",
        color="blue",
        marker="o",
        s=80,
        alpha=0.7,
        edgecolor="gray",
        linewidth=0.5,
        label="Grade"
    )

    # (b) Dibujamos 'refine_grade' en morado como diamantes
    sns.scatterplot(
        data=df,
        x="filename",
        y="refine_grade",
        color="purple",
        marker="D",
        s=100,
        alpha=0.8,
        edgecolor="black",
        linewidth=0.7,
        label="Refine"
    )

    # (c) Dibujamos 'expected_grade' en naranja como cruces
    sns.scatterplot(
        data=df_expected,
        x="filename",
        y="expected_grade",
        color="orange",
        marker="X",
        s=110,
        alpha=1.0,
        edgecolor="black",
        linewidth=1.0,
        label="Expected"
    )

    # 4) Ajustes estéticos
    plt.title("Comparación de notas por fichero\n(Grade vs. Refine Grade vs. Expected Grade)")
    plt.ylabel("Nota")
    plt.xlabel("Fichero")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()

    # 5) Guardamos la figura con timestamp
    salida_base = Path(__file__).resolve().parent / "outputs"
    salida_base.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fichero_unificado = salida_base / f"{timestamp}_{name}_all_in_one.png"
    plt.savefig(fichero_unificado)
    plt.close()

    print(f"✔ Gráfico combinado guardado en: {fichero_unificado}")

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

    expected_grades = {
        "test/Fibonacci/good.c": 9.0,
        "test/Fibonacci/regular.c": 8.0,
        "test/Fibonacci/iterative.c": 8.75,
        "test/Fibonacci/dynamic.c": 9.0,
        "test/Fibonacci/formula.c": 10.0
    }

    plot_variations(all_results, expected_grades, "Fibonnacci")
    plot_variation(all_results, "FIB")
    # compute_metrics(all_results, expected_grades)

def main():

    from sentence_transformers import SentenceTransformer

    # Descarga una vez
    # model = SentenceTransformer('all-MiniLM-L6-v2')
    # model.save('./resources/models/all-MiniLM-L6-v2')
    test_fib()

if __name__ == '__main__':
    main()
