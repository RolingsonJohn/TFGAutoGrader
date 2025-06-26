import uuid
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class LLMAgent(models.Model):
    """
        Modelo que representa el agente LLM
        que se empleará para la evaluación.
        Actualmente solo están disponibles:
            - ollama
            - groq
            - Genai
        Se debe especificar el nombre del agente
        y la API_KEY en caso de que esta sea necesaria.
    """
    name = models.CharField(
        max_length=200, unique=True, help_text="", default="ollama")
    
    api_key = models.CharField(max_length=200, unique=False, null=True, blank=True, help_text="")

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class LLMModel(models.Model):
    """
        Modelo LLM que se empleará para la
        evaluación. Debe ser un modelo disponible en los
        agentes.
        Se debe especificar el agente concreto y el nombre del modelo.
    """
    name = models.CharField(
        max_length=200, unique=True, help_text="")
    agent = models.ForeignKey(LLMAgent, default="ollama", on_delete=models.SET_DEFAULT, null=False)

    class Meta:
        ordering = ['agent']

    def __str__(self):
        return self.name


class Task(models.Model):
    """
        Modelo que representa el conjunto
        de documentos a evaluar por parte del
        modelo LLM. 
        Se debe especificar las rúbricas a emplear,
        el tema del ejercicio, el lenguaje de programación,
        los ejercicios comprimidos en zip y el modelo a utilizar.
    """
    STATUS_CHOICES = [
        ('PENDING',   'En proceso'),
        ('SUCCESS',   'Completado'),
        ('ERROR',     'Error'),
    ]

    user           = models.ForeignKey(User, on_delete=models.CASCADE)
    model          = models.ForeignKey(LLMModel, on_delete=models.SET_NULL, null=True)
    prog_lang      = models.CharField(max_length=25, default='C')
    theme          = models.CharField(max_length=200)
    status         = models.CharField(
                        max_length=10,
                        choices=STATUS_CHOICES,
                        default='PENDING'
                      )
    error_message  = models.TextField(null=True, blank=True)
    rubric_file    = models.FileField(upload_to='rubrics/')
    exercise_file  = models.FileField(upload_to='exercises/')
    created_at     = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Task {self.id} ({self.get_status_display()})"


class TaskResult(models.Model):
    """
    Almacena cada resultado devuelto por la herramienta de
    evaluación.
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='results'
    )
    data = models.JSONField(
        help_text="JSON con los datos de resultado del procesamiento"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Result for Task {self.task_id} at {self.created_at.isoformat()}"
    

class CodeExample(models.Model):
    """
        Representa los modelos que serán utilizados en el RAG,
        y permite su visualización.
    """
    user       = models.ForeignKey(User, on_delete=models.CASCADE)
    theme      = models.CharField(max_length=200)
    prog_lang  = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.theme} ({self.prog_lang})"


class CodeExampleFile(models.Model):
    """
        Almacena los ejemplos que serán utilizados en el RAG
    """
    example = models.ForeignKey(
        CodeExample,
        on_delete=models.CASCADE,
        related_name='files'
    )
    file    = models.FileField(upload_to='examples/')

    def __str__(self):
        return f"{self.file.name}"


