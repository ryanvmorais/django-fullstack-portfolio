"""
🚀 PROJETO: CONFIGURAÇÃO DO APLICATIVO (APPS.PY)
🎯 Objetivo: Educacional - Definir metadados e comportamentos globais do app.

ESTRUTURA DO CÓDIGO:
1. REGISTRO DO APP: Definição do nome interno e nome de exibição.
"""

from django.apps import AppConfig


# A classe AppConfig permite configurar detalhes específicos do aplicativo
class AppPortfolioConfig(AppConfig):
    # Define o tipo de campo de chave primária (ID) padrão para todos os modelos do app.
    # BigAutoField é recomendado para suportar um número massivo de registros (IDs longos).
    default_auto_field = "django.db.models.BigAutoField"

    # O nome real da pasta/módulo do seu aplicativo no sistema de arquivos.
    name = "app_portfolio"

    # --- TOQUE SÊNIOR ---
    # verbose_name: É como o nome do aplicativo aparecerá no Painel Administrativo.
    # Sem isso, o Django exibiria apenas "App_Portfolio". Com isso, fica profissional: "Gestão do Portfólio".
    verbose_name = "Gestão do Portfólio"
