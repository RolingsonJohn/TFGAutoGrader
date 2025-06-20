import io
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from grader.models import Task, TaskResult, CodeExample, LLMAgent, LLMModel, CodeExampleFile

@override_settings(MEDIA_ROOT='/tmp/django_test_media')
class GraderTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'testuser'
        self.password = 'pass1234'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.agent = LLMAgent.objects.create(name='test-agent', api_key='dummy')
        self.model = LLMModel.objects.create(name='test-model', agent=self.agent)


    def test_login_logout(self):
        # Primero: sin login acceder a tasks redirige a login
        response = self.client.get(reverse('tasks'))
        self.assertEqual(response.status_code, 302)
        login_url = reverse('account_login')
        self.assertTrue(response['Location'].startswith(login_url))
        # Ahora login
        login = self.client.login(username=self.username, password=self.password)
        self.assertTrue(login)

        print(self.client)
        # Con sesión activa, acceder a tasks debe devolver 200
        response = self.client.get(reverse('tasks'))
        self.assertEqual(response.status_code, 200)
        
        # Logout usando GET (Allauth permite GET de logout)
        response = self.client.get(reverse('account_logout'))
        self.assertEqual(response.status_code, 200)

        print(response)
        # Tras logout, de nuevo acceder a tasks redirige a login con next
        response = self.client.get(reverse('tasks'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login')


    def test_registration_view(self):
        url = reverse('account_signup')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpass123',
            'password2': 'newpass123',
        }
        response = self.client.post(url, data)
        # Allauth suele redirigir tras signup
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())


    def test_create_task_and_delete(self):
        # Login
        self.client.login(username=self.username, password=self.password)
        # Crear tarea
        url_create = reverse('task-create')
        rubric = SimpleUploadedFile('rubric.json', b'{}', content_type='application/json')
        exercise = SimpleUploadedFile('exercise.zip', b'PK\x03\x04', content_type='application/zip')
        data = {
            'theme': 'Tema prueba',
            'prog_lang': 'Python',
            'model': 1,
            'rubric_file': rubric,
            'exercise_file': exercise,
        }
        response = self.client.post(url_create, data)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(user=self.user, theme='Tema prueba')

        # Simular tarea procesada y resultado
        task.state = True
        task.save()
        TaskResult.objects.create(task=task, data=[{'filename': 'f.py', 'grade': 10}])

        # Borrar ejemplo
        url_del = reverse('delete_task', args=[task.id])
        response = self.client.post(url_del)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CodeExample.objects.filter(id=task.id).exists())


    def test_create_task_and_download_csv(self):
        # Login
        self.client.login(username=self.username, password=self.password)
        # Crear tarea
        url_create = reverse('task-create')
        rubric = SimpleUploadedFile('rubric.json', b'{}', content_type='application/json')
        exercise = SimpleUploadedFile('exercise.zip', b'PK\x03\x04', content_type='application/zip')
        data = {
            'theme': 'Tema prueba',
            'prog_lang': 'Python',
            'model': 1,
            'rubric_file': rubric,
            'exercise_file': exercise,
        }
        response = self.client.post(url_create, data)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(user=self.user, theme='Tema prueba')

        # Simular tarea procesada y resultado
        task.state = True
        task.save()
        TaskResult.objects.create(task=task, data=[{'filename': 'f.py', 'grade': 10}])

        # Descargar CSV
        url_csv = reverse('download_task_csv', args=[task.id])
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode()
        self.assertIn('filename,grade', content)
        self.assertIn('f.py,10', content)


    def test_code_example_upload_and_delete(self):
        # Login
        self.client.login(username=self.username, password=self.password)
        # Subir ejemplos
        url_create = reverse('example-create')
        code1 = SimpleUploadedFile('a.py', b'print(1)', content_type='text/x-python')
        code2 = SimpleUploadedFile('b.c', b'int main() { return 0; }', content_type='text/x-c')
        # Para Django Test Client, los files van dentro de data
        data = {
            'theme': 'Ejemplo Test',
            'prog_lang': 'C',
            'files': [code1, code2],
        }
        response = self.client.post(url_create, data)
        self.assertEqual(response.status_code, 302)
        example = CodeExample.objects.get(user=self.user, theme='Ejemplo Test')

        # Comprobar que se guardaron ambos ficheros
        self.assertEqual(example.files.count(), 2)

        # Borrar ejemplo
        url_del = reverse('example-delete', args=[example.id])
        response = self.client.post(url_del)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CodeExample.objects.filter(id=example.id).exists())


    def test_csrf_protection_on_task_create(self):
        # Usar cliente con verificación de CSRF
        csrf_client = Client(enforce_csrf_checks=True)
        self.client.login(username=self.username, password=self.password)
        # Intentar POST sin token CSRF
        url = reverse('task-create')
        data = {
            'theme': 'Tema CSRF',
            'prog_lang': 'Python',
            'model': self.model.id,
        }
        response = csrf_client.post(url, data)
        self.assertEqual(response.status_code, 403)


    def test_xss_prevention_in_example_detail(self):
        # Login
        self.client.login(username=self.username, password=self.password)
        # Crear ejemplo con contenido malicioso
        example = CodeExample.objects.create(
            user=self.user,
            theme='XSS Test',
            prog_lang='Python'
        )
        xss_content = b"<script>alert('xss')</script>"
        f = SimpleUploadedFile('xss.py', xss_content, content_type='text/x-python')
        CodeExampleFile.objects.create(example=example, file=f)

        url = reverse('example-detail', args=[example.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # No debe contener la etiqueta script sin escapar
        self.assertNotContains(response, "<script>alert('xss')</script>")
        # Debe contener la versión escapada
        # Verificar la versión escapada con comillas simples como &#x27;
        self.assertContains(response, "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;")