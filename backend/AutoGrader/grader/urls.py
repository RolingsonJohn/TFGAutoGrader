from . import views
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('tasks/', views.TaskTable.as_view(), name='tasks'),
    path('task/create', views.TaskCreate.as_view(), name='task-create'),
    path('task/<int:task_id>/results/', views.mark_task_as_processed, name='mark_task_as_processed'),
    path('task/<int:task_id>/error/',   views.receive_task_error,  name='receive_task_error'),
    path('task/<int:task_id>/download_csv', views.download_task_csv, name='download_task_csv'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('task/load_agents/', views.load_agents, name='load_agents'),
    path('examples/', views.example_list, name='examples'),
    path('examples/create/', views.create_code_example, name='example-create'),
    path('examples/<int:example_id>/', views.example_detail, name='example-detail'),
    path('examples/<int:example_id>/delete/', views.delete_example, name='example-delete'),
    path('', RedirectView.as_view(url='tasks/', permanent= True))
]