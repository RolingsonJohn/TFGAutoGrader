from pathlib import Path
from services.System import System

def process_files(theme: str, prog_lang: str, model_name: str, agent: str, api_key: str, token: str, zip_path: Path, rubric_path: Path):

    system = System(
        theme=theme,
        prog_lang=prog_lang,
        llm_model=model_name,
        agent=agent,
        api_key=api_key,
        token=token,
        zip_path=zip_path,
        rubric_path=rubric_path,
    )
    try:
        scripts = system.preevaluation()
        results = system.evaluation(scripts)
    except Exception as e:
        print(f"Error en la evaluación de los ficheros {e}")
        return None
    
    try:
        system.postevaluation(results, to_email="j.a.rolingson@gmail.com")
    except Exception as e:
        print(f"Error en la emisión del feedback a estudiantes {e}")

    return results


def upload_examples():
    pass
