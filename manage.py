#!/usr/bin/env python
"""
🛠️ PROJETO: UTILITÁRIO DE GERENCIAMENTO (MANAGE.PY)
🎯 Objetivo: Educacional - Interface de linha de comando para tarefas administrativas.

ESTRUTURA DO CÓDIGO:
1. CONFIGURAÇÃO: Aponta para o arquivo de configurações do projeto.
2. EXECUÇÃO: Processa os comandos digitados no terminal.
3. TRATAMENTO DE ERROS: Alerta sobre a ausência do Django ou do Virtualenv.
"""
import os
import sys

def main():
    """Executa as tarefas administrativas do Django."""
    
    # Define qual arquivo de configurações o Django deve usar para os comandos.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')
    
    try:
        # Tenta importar o executor de comandos do Django.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Se falhar, o erro mais comum é não ter ativado o ambiente virtual (venv).
        raise ImportError(
            "Não foi possível importar o Django. Verifique se ele está instalado "
            "e se o seu ambiente virtual (venv) está ativo."
        ) from exc
    
    # Pega o que você digitou no terminal (ex: runserver) e passa para o Django processar.
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
