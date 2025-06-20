from django.contrib import admin
from .models import *


@admin.register(LLMModel)
class LLMModelRegister(admin.ModelAdmin):
    list_display = ('name', 'agent')
    fields = ['name', 'agent']


@admin.register(LLMAgent)
class LLMAgentRegister(admin.ModelAdmin):
    list_display = ('name', 'api_key')
    fields = ['name', 'api_key']