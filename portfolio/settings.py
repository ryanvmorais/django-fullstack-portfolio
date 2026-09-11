"""
⚙️ PROJETO: CONFIGURAÇÕES DO DJANGO (SETTINGS.PY)
🎯 Objetivo: Educacional - Centralizar as configurações do sistema e segurança.

ESTRUTURA DO CÓDIGO:
1. AMBIENTE E SEGURANÇA BÁSICA: Importação de variáveis e chaves secretas.
2. MIDDLEWARES E APPS: Definição de recursos e camadas de processamento.
3. ESTÁTICOS E MÍDIA: Gerenciamento de arquivos CSS, JS e Imagens.
4. SEGURANÇA AVANÇADA (PRODUÇÃO): Configurações de SSL, CSP e Headers.
5. SERVIÇOS EXTERNOS: Configuração de E-mail (SMTP) e Cache.
"""

import os
import ssl
from pathlib import Path

import certifi
from dotenv import load_dotenv

# --- 1. AMBIENTE E SEGURANÇA BÁSICA ---

# Localização do Projeto: Define o diretório raiz para referências de caminhos
BASE_DIR = Path(__file__).resolve().parent.parent

# Carregamento de Variáveis: Busca o arquivo .env usando o caminho absoluto (Garante o deploy)
# Nota: O uso do operador / (pathlib) é a forma moderna e robusta de gerenciar caminhos no Python 3.10+
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# A SECRET_KEY é a "digital" do seu site. Nunca a exponha no GitHub!
SECRET_KEY = os.getenv("SECRET_KEY")

# Validação Crítica: Impede que o servidor suba sem a chave de segurança
# Sênior tip: Exibir o caminho procurado facilita o debug em ambientes de VPS/PaaS
if not SECRET_KEY:
    raise ValueError(
        f"ERRO: A variável SECRET_KEY não foi encontrada no arquivo .env! Caminho verificado: {env_path}"
    )

# DESENVOLVIMENTO: DEBUG = True (Erros detalhados) | PRODUÇÃO: DEBUG = False (Segurança total)
# O padrão 'False' é uma medida de "segurança por padrão" (secure by default)
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Em produção, o link do admin deve ser alterado no .env para dificultar ataques
# Isso evita o brute-force em /admin/ que é o alvo padrão de bots
ADMIN_URL_PATH = os.getenv("ADMIN_URL", "admin/")

# Define quais domínios podem acessar o site (Segurança de cabeçalho Host)
# No .env use: ALLOWED_HOSTS=djangofullstackportfolio.pythonanywhere.com
ALLOWED_HOSTS = ["*"] if DEBUG else os.getenv("ALLOWED_HOSTS", "").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app_portfolio.apps.AppPortfolioConfig",
]

# --- 2. MIDDLEWARES (Camadas de Processamento) ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Gerencia arquivos estáticos de forma eficiente
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",  # Proteção contra Content Security Policy
]

ROOT_URLCONF = "portfolio.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "portfolio.wsgi.application"

# Banco de dados padrão (SQLite para desenvolvimento rápido)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --- 3. ESTÁTICOS E MÍDIA ---

# URL base para acessar os arquivos via navegador
STATIC_URL = "static/"

# Onde o Django busca arquivos estáticos durante o desenvolvimento
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# Onde o Django vai "REUNIR" todos os arquivos para a produção
# É desta pasta que o PythonAnywhere vai ler o CSS/JS
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Configurações de Mídia (Uploads de imagens, etc.)
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# WhiteNoise: Comprime e faz cache de arquivos estáticos para maior velocidade
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# --- 4. SEGURANÇA AVANÇADA (SÊNIOR) ---

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"  # Impede que seu site seja exibido dentro de iframes alheios

# CSP: Define de onde o seu site pode carregar scripts, estilos e imagens
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_SCRIPT_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")

# LOGICA DE PRODUÇÃO: Ativa proteção rigorosa apenas se DEBUG for False
if not DEBUG:
    # Estas linhas forçam o uso de HTTPS. Se ativadas localmente, o site não abre!
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS: Avisa ao navegador para usar SEMPRE HTTPS por 1 ano
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# --- 5. SERVIÇOS EXTERNOS (E-MAIL E CACHE) ---

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_PASS")
DEFAULT_FROM_EMAIL = f"Projeto Portfólio <{EMAIL_HOST_USER}>"

# Certificado SSL necessário para que o Python 3.10+ consiga falar com o Gmail
EMAIL_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Cache em memória: Utilizado pelo nosso sistema de Rate Limit (Proteção contra spam)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
