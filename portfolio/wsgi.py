"""
🌐 PROJETO: INTERFACE DE SERVIDOR (WSGI.PY)
🎯 Objetivo: Educacional - Estabelecer a comunicação padrão para o deploy em produção.

ESTRUTURA DO CÓDIGO:
1. DIRECIONAMENTO: Aponta para as configurações centrais do projeto.
2. INSTÂNCIA WSGI: Cria a ponte de comunicação síncrona com o servidor.
"""

import os

from django.core.wsgi import get_wsgi_application

# O Django precisa saber onde as configurações (settings.py) estão localizadas.
# Este comando define o caminho padrão para o módulo de configurações do projeto.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio.settings")

# Esta variável 'application' é o ponto de entrada que o servidor (ex: Gunicorn)
# usará para "chamar" o Django e processar as requisições dos visitantes.
application = get_wsgi_application()
