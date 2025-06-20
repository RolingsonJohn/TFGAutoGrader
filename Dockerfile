FROM python:3.12.3

WORKDIR /app

COPY fastapi_app/requirements.txt .

RUN pip install --no-cache-dir --timeout 60 -r requirements.txt

COPY fastapi_app .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]