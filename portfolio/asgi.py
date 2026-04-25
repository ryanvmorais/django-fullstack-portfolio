"""
⚡ PROJETO: INTERFACE ASSÍNCRONA (ASGI.PY)
🎯 Objetivo: Educacional - Permitir comunicações em tempo real e alta performance.

ESTRUTURA DO CÓDIGO:
1. AMBIENTE: Definição do arquivo de configurações padrão.
2. INSTÂNCIA ASGI: Criação do canal de comunicação assíncrona.
"""

import os
from django.core.asgi import get_asgi_application

# O comando setdefault garante que o servidor saiba exatamente onde
# encontrar o seu arquivo 'settings.py' ao iniciar o processo.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')

# 'application' é a variável que o seu servidor de produção (como o Daphne ou Uvicorn)
# procurará para colocar o site no ar.
application = get_asgi_application()
