"""
🧠 PROJETO: LÓGICA DE VISUALIZAÇÃO (VIEWS.PY)
🎯 Objetivo: Educacional - Processar dados do banco e gerenciar interações do usuário.

ESTRUTURA DO CÓDIGO:
1. CONSULTAS OTIMIZADAS (GET): Busca eficiente de dados para a Home.
2. CAMADA DE SEGURANÇA: Honeypot, Rate Limit e Sanitização de HTML.
3. COMUNICAÇÃO EXTERNA: Processamento do formulário e envio de E-mail (SMTP).
4. RESPOSTAS HÍBRIDAS: Suporte para navegação comum e requisições AJAX (JSON).
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import bleach
from .forms import MensagemContatoForm
from .models import (
    Projeto,
    CategoriaProjeto,
    Perfil,
    Tecnologia,
    CategoriaHabilidade,
    Estatistica,
)

def home(request):
    # --- 1. BUSCAR DADOS DO BANCO (GET) ---
    perfil = Perfil.objects.first()
    
    # PERFORMANCE SÊNIOR: select_related e prefetch_related evitam o erro de "N+1 consultas" no banco
    projetos = Projeto.objects.select_related('categoria_projeto').prefetch_related('tecnologias').all()
    
    tech_icons = Tecnologia.objects.filter(mostrar_no_home=True).order_by('ordem', 'nome')
    estatisticas = Estatistica.objects.all()
    categorias_projetos = CategoriaProjeto.objects.all()
    categorias_habilidades = CategoriaHabilidade.objects.prefetch_related('habilidades').all()
    
    # Inicializa o formulário vazio para exibição inicial
    form = MensagemContatoForm()

    # --- 2. LÓGICA DO FORMULÁRIO DE CONTATO (POST) ---
    if request.method == 'POST':
        
        # A. SEGURANÇA: HONEYPOT CHECK
        # Se o campo invisível estiver preenchido, é um robô. Redirecionamos silenciosamente.
        honeypot = request.POST.get('honeypot')
        if honeypot:
            return redirect('home')

        # B. SEGURANÇA: RATE LIMIT (Controle de Fluxo)
        # Identifica o IP e bloqueia envios repetitivos para evitar ataques ou custos de SMTP.
        user_ip = request.META.get('REMOTE_ADDR')
        cache_key = f'contact_limit_{user_ip}'
        if cache.get(cache_key):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Muitas tentativas...'}, status=429)
            messages.error(request, "Você já enviou uma mensagem recentemente. Por favor, aguarde 10 minutos.")
            return redirect('home')

        form = MensagemContatoForm(request.POST)
        
        if form.is_valid():
            # C. SEGURANÇA: SANITIZAÇÃO (Bleach)
            # Remove qualquer tag HTML maliciosa enviada no campo de mensagem (Proteção XSS).
            mensagem_limpa = bleach.clean(form.cleaned_data['mensagem'], tags=[], strip=True)
            
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
                    [settings.EMAIL_HOST_USER],
                    fail_silently=False,
                )
                
                # Ativa o bloqueio de 10 min (600s) no cache após o envio com sucesso
                cache.set(cache_key, True, 600)

                # Suporte para respostas assíncronas (AJAX)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'success', 'message': 'Mensagem enviada!'})
                return redirect('home')

            except Exception as e:
                print(f"Erro SMTP: {e}")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Erro ao enviar e-mail.'}, status=500)
        
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Dados inválidos.'}, status=400)

    # --- 3. CONTEXTO PARA O TEMPLATE ---
    # Dicionário que mapeia variáveis do Python para as tags {{ }} no HTML.
    context = {
        'perfil': perfil,
        'form': form,
        'projetos': projetos,
        'categorias_habilidades': categorias_habilidades,
        'tech_icons': tech_icons,
        'estatisticas': estatisticas,
        'categorias_projetos': categorias_projetos,
    }
    
    return render(request, 'home.html', context)