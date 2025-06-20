import json
import requests
import pandas as pd
import io
import zipfile
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponse
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.views import generic
from django.views.decorators.http import require_POST
from .models import Task, LLMModel, TaskResult, CodeExample, CodeExampleFile
from .forms import TaskForm, CodeExampleForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import  login_required

API_BASE = "http://localhost:8001"


@login_required
def example_list(request):
    examples = CodeExample.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'config/examples_list.html', {'examples': examples})


@login_required
def create_code_example(request):
    if request.method == 'POST':
        form = CodeExampleForm(request.POST, request.FILES)
        if form.is_valid():
            example = form.save(commit=False)
            example.user = request.user
            example.save()
            # Guardamos ficheros y los enviamos al RAG
            for f in request.FILES.getlist('files'):
                cef = CodeExampleFile.objects.create(example=example, file=f)
                # Leer contenido y notificar a FastAPI
                code_text = cef.file.read().decode('utf-8', errors='ignore')
                payload = {
                    "title": example.theme,
                    "description": f"Ejemplo de {example.theme}",
                    "code": code_text,
                    "theme": [example.theme],
                }
                try:
                    requests.post(f"{API_BASE}/examples/populate", json=payload, timeout=5).raise_for_status()
                except Exception as e:
                    print("Error al notificar RAG:", e)
            return redirect('examples')
    else:
        form = CodeExampleForm()
    return render(request, 'config/examples_create.html', {'form': form})


@login_required
def example_detail(request, example_id):
    example = get_object_or_404(CodeExample, id=example_id, user=request.user)
    files = []
    for f in example.files.all():
        # Asegúrate de posicionarte al inicio
        f.file.open(mode='rb')
        raw = f.file.read()
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            text = raw.decode('latin-1', errors='ignore')
        files.append({
            'name': f.file.name.split('/')[-1],  # solo nombre
            'content': text
        })
        f.file.close()

    return render(request, 'config/examples_detail.html', {
        'example': example,
        'files': files
    })

@require_POST
@login_required
def delete_example(request, example_id):
    example = get_object_or_404(CodeExample, id=example_id, user=request.user)
    # notificar borrado al RAG
    try:
        requests.post(f"{API_BASE}/examples/delete/", json={'title': example.theme}, timeout=5)
    except Exception as e:
        print("Error notificando borrado RAG:", e)
    example.delete()
    return redirect('examples')


def load_agents(request):
    model_id = request.GET.get('model')

    if str(model_id).strip() == '' or model_id == None:
        return render(request, 'tasks/agents_options.html', {'agent': None})
    model = get_object_or_404(LLMModel, id=model_id)
    agent = model.agent
    return render(request, 'tasks/agents_options.html', {'agent': agent})



@require_POST
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return redirect('tasks') 


@csrf_exempt
def mark_task_as_processed(request, task_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:

        payload = json.loads(request.body)
        task = Task.objects.get(id=task_id)
        task.status = 'SUCCESS'
        task.save()
        TaskResult.objects.create(task=task, data=payload.get('result', {}))

        return JsonResponse({'message': f'Task {task_id} result saved.'})
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Unknown Error'}, status=500)
    

@csrf_exempt
def receive_task_error(request, task_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        payload = json.loads(request.body)
        task = Task.objects.get(id=task_id)
        task.status = 'ERROR'
        task.error_message = payload.get('error', 'Unknown error')
        task.save()
        return JsonResponse({'message': 'Error recorded.'})
    except Task.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    

def download_task_csv(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        results = task.results.all().order_by('created_at')

        rows = []
        for r in results:
            ts = r.created_at.isoformat()
            # cada r.data es la lista all_results
            for item in r.data:
                # copia y añade el timestamp
                row = item.copy()
                row['created_at'] = ts
                rows.append(row)

        # columnas en el orden que desees
        columns = [
            'created_at',
            'filename',
            'grade',
            'refine_grade',
            'feedback',
            'refine_feedback'
        ]

        # DataFrame y aseguramos el orden de columnas
        df = pd.DataFrame(rows)
        df = df.reindex(columns=columns)

        # construimos la respuesta CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="task_{task_id}_results.csv"'
        )
        df.to_csv(path_or_buf=response, index=False, na_rep='')

        return response

    except Task.DoesNotExist:
        return HttpResponse(status=404)


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"


class TaskTable(LoginRequiredMixin, generic.ListView):
    model = Task
    #permission_required = 'grader.normal'
    template_name = 'tasks/task_table.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).order_by('-created_at')


class TaskCreate(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_create.html'
    success_url = reverse_lazy('tasks')

    def form_valid(self, form):
        form.instance.user = self.request.user
        task = form.save(commit=False)
        task.save()
        print(task.id, task.theme, task.model, task.prog_lang, task.model.agent)
        try:
            account = SocialAccount.objects.get(user=self.request.user, provider='microsoft')
            token = account.socialtoken_set.all().order_by('-expires_at').first()
            print(token.token, account)

            header = {
                "Authorization" : f"Bearer {token.token}"
            }
        except Exception as e:
            print(e)
            header = {
                "Authorization" : f"Bearer None"
            }

        
        data = {
            "task_id": task.id,
            "theme": task.theme,
            "prog_lang": task.prog_lang,
            "model": task.model.name if hasattr(task.model, "name") else str(task.model),
            "agent": task.model.agent.name if hasattr(task.model.agent, "name") else str(task.model.agent),
            "api_key": task.model.agent.api_key,
        }

        # Preparar archivos
        files = {
            "rubrics_file": (
                task.rubric_file.name,
                task.rubric_file.file,
                "application/json"
            ),
            "compressed_file": (
                task.exercise_file.name,
                task.exercise_file.file,
                "application/zip"
            )
        }

        try:
            response = requests.post(f"{API_BASE}/evaluate", headers=header, data=data, files=files)
            response.raise_for_status()
            print(self.request, "Task created and sent for evaluation!")
        except requests.exceptions.RequestException as e:
            print(self.request, f"Error sending task for evaluation: {e}")
            #return super().form_invalid(form)
        
        return super().form_valid(form)

    