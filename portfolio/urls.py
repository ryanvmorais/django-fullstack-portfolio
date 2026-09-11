"""
🌐 PROJETO: ROTEAMENTO GLOBAL (PORTFOLIO/URLS.PY)
🎯 Objetivo: Educacional - Centralizar as rotas do sistema e gerenciar arquivos estáticos.

ESTRUTURA DO CÓDIGO:
1. SEGURANÇA ADMINISTRATIVA: Ofuscação da URL do painel de controle.
2. MODULARIZAÇÃO: Inclusão das rotas específicas da aplicação do portfólio.
3. AMBIENTE DE DESENVOLVIMENTO: Configuração para exibição local de fotos e mídia.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

# O urlpatterns global serve como a porta de entrada principal do servidor.
urlpatterns = [
    # 1. ADMINISTRAÇÃO DINÂMICA
    # Em vez de usar 'admin/', usamos uma variável do settings para evitar
    # que invasores encontrem facilmente a tela de login.
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    # 2. INCLUSÃO DE APLICATIVOS (MODULARIZAÇÃO)
    # Aqui dizemos ao Django: "Se o usuário acessar a raiz (''),
    # procure as instruções dentro do arquivo urls.py da pasta app_portfolio".
    path("", include("app_portfolio.urls")),
    # 3. GESTÃO DE ARQUIVOS ESTÁTICOS
    # Redireciona a busca automática do navegador para o local correto do favicon.
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "icons/favicon.png"),
    ),
]

# --- 3. GESTÃO DE ARQUIVOS DE MÍDIA (MODO DESENVOLVIMENTO) ---

# O Django, por segurança, não serve arquivos de imagem (Media) automaticamente.
# Esta lógica abaixo só funciona se o DEBUG estiver como True no seu .env.
if settings.DEBUG:
    # static() cria uma rota temporária para que você consiga ver as fotos
    # dos projetos e do seu perfil enquanto desenvolve localmente.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
