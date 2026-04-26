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

from pathlib import Path
from dotenv import load_dotenv
import certifi
import os
import ssl

# --- 1. AMBIENTE E SEGURANÇA BÁSICA ---

# Carrega as variáveis do arquivo .env (Onde ficam senhas e chaves)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Em produção, o link do admin deve ser alterado no .env para segurança
ADMIN_URL_PATH = os.getenv('ADMIN_URL', 'admin/')

# A SECRET_KEY é a "digital" do seu site. Nunca a exponha no GitHub!
SECRET_KEY = os.getenv('SECRET_KEY')

# DESENVOLVIMENTO: DEBUG = True (Mostra erros detalhados)
# PRODUÇÃO: No .env, mude para DEBUG=False (Esconde erros do usuário final)
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# DESENVOLVIMENTO: '*' permite acessar de qualquer lugar localmente
# PRODUÇÃO: No .env, coloque apenas o seu domínio (ex: seu-nome.pythonanywhere.com)
ALLOWED_HOSTS = ['*'] if DEBUG else os.getenv('ALLOWED_HOSTS', '').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app_portfolio.apps.AppPortfolioConfig',
]

# --- 2. MIDDLEWARES (Camadas de Processamento) ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Gerencia arquivos estáticos de forma eficiente
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware' # Proteção contra Content Security Policy
]

ROOT_URLCONF = 'portfolio.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'portfolio.wsgi.application'

# Banco de dados padrão (SQLite para desenvolvimento rápido)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'pt-br' 
TIME_ZONE = 'America/Sao_Paulo' 
USE_I18N = True
USE_TZ = True

# --- 3. ESTÁTICOS E MÍDIA ---

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Pasta onde o comando collectstatic reunirá todos os arquivos para o deploy
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# WhiteNoise: Comprime e faz cache de arquivos estáticos para maior velocidade
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- 4. SEGURANÇA AVANÇADA (SÊNIOR) ---

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY' # Impede que seu site seja exibido dentro de iframes alheios

# CSP: Define de onde o seu site pode carregar scripts, estilos e imagens
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
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

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASS')
DEFAULT_FROM_EMAIL = f"Projeto Portfólio <{EMAIL_HOST_USER}>"

# Certificado SSL necessário para que o Python 3.10+ consiga falar com o Gmail
EMAIL_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# Cache em memória: Utilizado pelo nosso sistema de Rate Limit (Proteção contra spam)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}