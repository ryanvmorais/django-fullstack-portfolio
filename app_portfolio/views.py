"""
🧠 PROJETO: LÓGICA DE VISUALIZAÇÃO (VIEWS.PY)
🎯 Objetivo: Educacional - Processar dados do banco e gerenciar interações do usuário.

ESTRUTURA DO CÓDIGO:
1. CONSULTAS OTIMIZADAS (GET): Busca eficiente de dados para a Home.
2. CAMADA DE SEGURANÇA: Honeypot, Rate Limit e Sanitização de HTML.
3. COMUNICAÇÃO EXTERNA: Processamento do formulário e envio de E-mail (SMTP).
4. RESPOSTAS HÍBRIDAS: Suporte para navegação comum e requisições AJAX (JSON).
"""

import logging

import bleach
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render

from .forms import MensagemContatoForm
from .models import (
    CategoriaHabilidade,
    CategoriaProjeto,
    Estatistica,
    Perfil,
    Projeto,
    Tecnologia,
)

# Frases mostradas ao visitante quando o envio não vai adiante (spec 004,
# RF-03): o JavaScript exibe `message` das respostas JSON, e o limite de envio
# usa a mesma frase no fluxo HTML tradicional (django.contrib.messages).
MENSAGEM_ENVIADO = "Mensagem enviada!"
MENSAGEM_LIMITE_ENVIO = (
    "Você já enviou uma mensagem recentemente. Aguarde 10 minutos para enviar outra."
)
MENSAGEM_FALHA_ENVIO = (
    "Não foi possível enviar agora. Tente novamente em alguns minutos."
)
MENSAGEM_DADOS_INVALIDOS = "Confira os campos do formulário e tente novamente."

logger = logging.getLogger(__name__)


def home(request: HttpRequest) -> HttpResponse:
    """
    Renderiza a Home e processa o formulário de contato (GET + POST).

    No POST, aplica em sequência honeypot, validação do formulário, rate
    limit por IP (reserva atômica via ``cache.add()``) e sanitização (Bleach)
    antes de salvar a mensagem e disparar o e-mail de notificação. Responde em
    HTML (navegação comum) ou JSON (requisição AJAX, identificada pelo header
    ``X-Requested-With``).

    Args:
        request (HttpRequest): Requisição GET (exibição) ou POST (envio do
            formulário de contato).

    Returns:
        HttpResponse: Página renderizada, redirect (fluxo HTML) ou
            :class:`~django.http.JsonResponse` (fluxo AJAX).
    """
    # --- 1. BUSCAR DADOS DO BANCO (GET) ---
    perfil = Perfil.objects.first()

    # PERFORMANCE SÊNIOR: select_related e prefetch_related evitam o erro de "N+1 consultas" no banco
    projetos = (
        Projeto.objects.select_related("categoria_projeto")
        .prefetch_related("tecnologias")
        .all()
    )

    tech_icons = Tecnologia.objects.filter(mostrar_no_home=True).order_by(
        "ordem", "nome"
    )
    estatisticas = Estatistica.objects.all()
    categorias_projetos = CategoriaProjeto.objects.all()
    categorias_habilidades = CategoriaHabilidade.objects.prefetch_related(
        "habilidades"
    ).all()

    # Inicializa o formulário vazio para exibição inicial
    form = MensagemContatoForm()

    # --- 2. LÓGICA DO FORMULÁRIO DE CONTATO (POST) ---
    if request.method == "POST":

        # A. SEGURANÇA: HONEYPOT CHECK
        # Se o campo invisível estiver preenchido, é um robô. Redirecionamos silenciosamente.
        honeypot = request.POST.get("honeypot")
        if honeypot:
            return redirect("home")

        form = MensagemContatoForm(request.POST)

        if form.is_valid():
            # B. SEGURANÇA: RATE LIMIT (Controle de Fluxo)
            # cache.add() só grava se a chave ainda não existir -- operação
            # atômica que reserva o slot antes de processar o envio. Um
            # cache.get() + cache.set() posterior (versão anterior) permite
            # que requisições concorrentes passem pela checagem antes que a
            # primeira grave o bloqueio, e todas completem o envio de e-mail
            # (achado da auditoria de segurança: race condition CWE-362).
            user_ip = request.META.get("REMOTE_ADDR")
            cache_key = f"contact_limit_{user_ip}"
            if not cache.add(cache_key, True, 600):
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {"status": "error", "message": MENSAGEM_LIMITE_ENVIO},
                        status=429,
                    )
                messages.error(request, MENSAGEM_LIMITE_ENVIO)
                return redirect("home")

            # C. SEGURANÇA: SANITIZAÇÃO (Bleach)
            # Remove qualquer tag HTML maliciosa enviada no campo de mensagem (Proteção XSS).
            mensagem_limpa = bleach.clean(
                form.cleaned_data["mensagem"], tags=[], strip=True
            )

            mensagem_obj = form.save(commit=False)
            mensagem_obj.mensagem = mensagem_limpa
            mensagem_obj.save()

            # D. COMUNICAÇÃO: ENVIO DE E-MAIL (SMTP)
            try:
                assunto_email = f"Novo Contato: {mensagem_obj.assunto}"
                corpo_email = (
                    f"Mensagem de: {mensagem_obj.nome}\n"
                    f"E-mail: {mensagem_obj.email}\n\n"
                    f"Conteúdo:\n{mensagem_obj.mensagem}"
                )

                send_mail(
                    assunto_email,
                    corpo_email,
                    settings.EMAIL_HOST_USER,
                    [settings.EMAIL_HOST_USER],  # type: ignore[list-item]
                    # EMAIL_HOST_USER vem do .env; se ausente, o send_mail
                    # falha aqui dentro e cai no except abaixo (comportamento
                    # já esperado, não um caso a modelar no tipo).
                    fail_silently=False,
                )

                # Suporte para respostas assíncronas (AJAX)
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {"status": "success", "message": MENSAGEM_ENVIADO}
                    )
                messages.success(request, MENSAGEM_ENVIADO)
                return redirect("home")

            except Exception:
                logger.exception("Falha ao enviar e-mail de contato")
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse(
                        {"status": "error", "message": MENSAGEM_FALHA_ENVIO},
                        status=500,
                    )
                messages.error(request, MENSAGEM_FALHA_ENVIO)

        else:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse(
                    {"status": "error", "message": MENSAGEM_DADOS_INVALIDOS},
                    status=400,
                )
            messages.error(request, MENSAGEM_DADOS_INVALIDOS)

    # --- 3. CONTEXTO PARA O TEMPLATE ---
    # Dicionário que mapeia variáveis do Python para as tags {{ }} no HTML.
    context = {
        "perfil": perfil,
        "form": form,
        "projetos": projetos,
        "categorias_habilidades": categorias_habilidades,
        "tech_icons": tech_icons,
        "estatisticas": estatisticas,
        "categorias_projetos": categorias_projetos,
    }

    return render(request, "home.html", context)
