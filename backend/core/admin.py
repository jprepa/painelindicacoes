from django.contrib import admin
from .models import Parceiro

# Isso faz a mágica de criar o formulário automático
@admin.register(Parceiro)
class ParceiroAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'status', 'score_atual', 'ultima_indicacao')
    search_fields = ('empresa', 'contato_nome')