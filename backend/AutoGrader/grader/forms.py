# forms.py
from django import forms
from .models import Task, LLMModel, LLMAgent, CodeExample

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['theme', 'prog_lang', 'model', 'rubric_file', 'exercise_file']

        widgets = {
            'model': forms.Select(attrs={
                "hx-get": "load_agents/",
                "hx-target": "#agent-field",
                "hx-trigger": "change",
                "hx-vals": '{"model_id": this.value}'
            }),
            'agent': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class CodeExampleForm(forms.ModelForm):
    # Campo para subir múltiples ficheros .py o .c
    files = forms.FileField(
        widget=forms.FileInput(attrs={
            'accept': '.py,.c'
        }),
        help_text="Sube uno o varios ficheros .py o .c"
    )

    class Meta:
        model = CodeExample
        fields = ['theme', 'prog_lang', 'files']
        widgets = {
            'theme': forms.TextInput(attrs={'placeholder': 'Tema del ejercicio'}),
            'prog_lang': forms.TextInput(attrs={'placeholder': 'Lenguaje (e.g. C, Python)'}),
        }