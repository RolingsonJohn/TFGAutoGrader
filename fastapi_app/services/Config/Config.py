import os
from configparser import ConfigParser

"""
    Módulo de configuración de parámetros a partir de fichero config.ini
"""

config = ConfigParser()

_config_dir = os.path.dirname(__file__)
_config_path = os.path.join(_config_dir, 'config.ini')
config.read(_config_path)

# --- LLM Config ---
OLLAMA_MODEL = config.get("LLM", "OLLAMA_MODEL", fallback="llama3.1:latest")
GROQ_MODEL = config.get("LLM", "GROQ_MODEL", fallback="deepseek-r1-distill-llama-70b")
GENAI_MODEL = config.get("LLM", "GENAI_MODEL", fallback="gemini-2.0-flash")
MAX_THREADS = int(config.get("LLM", "MAX_THREADS", fallback=1))
API_KEY_GROQ = config.get("LLM", "API_KEY_GROQ")
API_KEY_GOOGLE = config.get("LLM", "API_KEY_GOOGLE")
EXE_METHOD = config.get("LLM", "EXE_METHOD", fallback="ollama")

# --- RAG Config ---
TOKENIZER = config.get("RAG", "TOKENIZER", fallback="sentence-transformers/codebert-base")
RAG_MODEL = config.get("RAG", "RAG_MODEL")
CLF_MODEL = config.get("RAG", "CLF_MODEL")

# --- Docker Config ---
DOCKER_HOST = config.get("DOCKER", "DOCKER_HOST", fallback="unix:///var/run/docker.sock")
DOCKER_IMAGE = config.get("DOCKER", "IMAGE", fallback="sandbox:1") # Added IMAGE

# --- Mail Config ---
AUTHORITY = config.get("AUTHORITY", "MAIL", fallback="https://login.microsoftonline.com/common")
SCOPES = config.get("SCOPES", "MAIL", fallback=["https://graph.microsoft.com/Mail.Send"])
CLIENT_ID = config.get("CLIENT_ID", "MAIL", fallback="57a0f8c5-a6a8-41b6-9a5b-a2b0a518f752")
ENDPOINT = config.get("CLIENT_ID", "MAIL", fallback="https://graph.microsoft.com/v1.0/me/sendMail")