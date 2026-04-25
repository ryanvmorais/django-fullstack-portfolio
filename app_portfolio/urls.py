"""
🗺️ PROJETO: ROTEAMENTO DE URLS (URLS.PY)
🎯 Objetivo: Educacional - Mapear endereços da web para funções de lógica (Views).

ESTRUTURA DO CÓDIGO:
1. MAPEAMENTO DE ROTAS: Definição de caminhos e nomes internos.
"""

from django.urls import path
from . import views

# O urlpatterns é uma lista que o Django percorre do topo para baixo
# para encontrar uma correspondência com o que foi digitado na barra de endereços.

urlpatterns = [
    # ROTA RAIZ (Home):
    # '' significa que este é o endereço principal (ex: www.seusite.com.br/)
    # views.home chama a função que processa os dados no banco
    # name='home' permite que você use o nome 'home' em vez do link fixo nos templates
    path('', views.home, name='home'),
]
