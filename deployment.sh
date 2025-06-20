#!/bin/bash

SESSION="tfg_services"
VENV_PATH="./venv"

tmux has-session -t $SESSION 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Cerrando sesión tmux anterior..."
    tmux kill-session -t $SESSION
fi

# Iniciar sesión tmux
tmux new-session -d -s $SESSION

# Ventana 1: Django (localhost:8000)
tmux rename-window -t $SESSION 'Django'
tmux send-keys -t $SESSION "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t $SESSION "cd backend/AutoGrader && python manage.py runserver localhost:8000" C-m

# Ventana 2: FastAPI (localhost:8001)
tmux new-window -t $SESSION -n 'FastAPI'
tmux send-keys -t $SESSION:1 "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t $SESSION:1 "cd fastapi_app && uvicorn main:app --reload --port 8001" C-m

# Ventana 3: Celery Worker
tmux new-window -t $SESSION -n 'Celery'
tmux send-keys -t $SESSION:2 "source $VENV_PATH/bin/activate" C-m
tmux send-keys -t $SESSION:2 "cd fastapi_app && celery -A worker worker --loglevel=info --queues=evaluations" C-m

tmux attach-session -t $SESSION
