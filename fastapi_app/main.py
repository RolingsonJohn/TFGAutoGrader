from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header, BackgroundTasks
import ollama
import requests
from pathlib import Path
from worker import process_files_and_notify

app = FastAPI()


@app.get("/listall")
async def listall():
    # Lists all available ollama models
    try:
        return ollama.list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def evaluate(
    authorization: str = Header(...),
    task_id: int = Form(...),
    theme: str = Form(...),
    prog_lang: str = Form(...),
    model: str = Form(...),
    agent: str = Form(...), 
    api_key: str = Form(...),
    compressed_file: UploadFile = File(...),
    rubrics_file: UploadFile = File(...)
):
    BASE_DIR = Path(__file__).resolve().parent
    dest_dir = BASE_DIR / "services/resources"
    dest_dir.mkdir(parents=True, exist_ok=True)

    zip_path = dest_dir / "compressed.zip"
    rubric_path = dest_dir / "rubrics.json"

    print(theme, prog_lang, model, agent, api_key, authorization, compressed_file, rubrics_file)

    token = authorization.split(' ')[1]
    zip_data = await compressed_file.read()
    rubric_data = await rubrics_file.read()

    try:
        with open(zip_path, "wb") as f1:
            f1.write(zip_data)
        print("ZIP guardado en:", zip_path)
    except Exception as e:
        print("Error ZIP:", e)

    try:
        with open(rubric_path, "wb") as f2:
            f2.write(rubric_data)
        print("JSON guardado en:", rubric_path)
    except Exception as e:
        print("Error JSON:", e)

    process_files_and_notify.delay(
        task_id, theme, prog_lang, model, agent,
        api_key, token, str(zip_path), str(rubric_path)
    )

    return {"message": "Evaluation completed successfully"}


@app.post("/examples/populate")
async def populate_rag():
    print("Poblando RAG")

@app.post("/examples/delete")
async def delete_example(
    task_id: int = Form(...),
    theme: str = Form(...),
    prog_lang: str = Form(...)):

    print("Poblando RAG")