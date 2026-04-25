"""
🧪 PROJETO: TESTES AUTOMATIZADOS (TESTS.PY)
🎯 Objetivo: Educacional - Validar a integridade, segurança e performance do sistema.

ESTRUTURA DO CÓDIGO:
1. FIXTURES: Configurações de ambiente para os testes (Limpeza e SSL).
2. TESTES DE CORE: Verificação de status code, criação de modelos e performance.
3. TESTES DE SEGURANÇA: Validação de XSS, Honeypot e Rate Limit.
"""

import pytest
from django.urls import reverse
from django.core.cache import cache
from app_portfolio.models import Perfil, MensagemContato

# --- 1. CONFIGURAÇÕES DE AMBIENTE (FIXTURES) ---

@pytest.fixture(autouse=True)
def clear_cache():
    """ Garante que o cache esteja limpo antes de cada teste de Rate Limit. """
    cache.clear()

@pytest.fixture(autouse=True)
def disable_ssl_redirect(settings):
    """ 
    Impedimos o redirecionamento HTTPS durante os testes para evitar 
    erros de conexão no ambiente de teste controlado. 
    """
    settings.SECURE_SSL_REDIRECT = False

# --- 2. TESTES DE CORE E PERFORMANCE ---

@pytest.mark.django_db # Permite que o teste acesse o banco de dados
class TestPortfolioCore:
    def test_home_status_code(self, client):
        """ Verifica se a página inicial está carregando (Status 200). """
        url = reverse('home')
        response = client.get(url)
        assert response.status_code == 200

    def test_perfil_creation(self):
        """ Valida se o modelo de Perfil está aceitando inserções corretamente. """
        Perfil.objects.create(nome="Dev Teste", cargo="Sênior")
        assert Perfil.objects.count() == 1
        
    def test_home_query_count(self, client, django_assert_max_num_queries):
        """ 
        TESTE SÊNIOR: Garante que a página inicial não ultrapasse 10 consultas ao banco.
        Isso previne lentidão causada pelo excesso de requisições (N+1).
        """
        with django_assert_max_num_queries(10):
            client.get(reverse('home'))

# --- 3. TESTES DE SEGURANÇA ---

@pytest.mark.django_db
class TestSegurancaContato:

    def test_contato_xss_sanitization(self, client):
        """ 
        Verifica se a sanitização (Bleach) está removendo tags maliciosas <script> 
        antes de salvar a mensagem no banco de dados. 
        """
        url = reverse('home')
        data = {
            'nome': 'Hacker',
            'email': 'hacker@evil.com',
            'assunto': 'Ataque',
            'mensagem': '<script>alert("xss")</script>Olá',
            'honeypot': ''
        }
        client.post(url, data, follow=True)
        
        msg = MensagemContato.objects.last()
        assert msg is not None
        assert "<script>" not in msg.mensagem # O script deve ter sido removido

    def test_rate_limit_blocking(self, client):
        """ 
        Valida o sistema de bloqueio. O primeiro envio deve passar, 
        o segundo (imediato) deve retornar uma mensagem de erro/aguarde. 
        """
        url = reverse('home')
        data = {'nome': 'U', 'email': 'u@t.com', 'assunto': 'O', 'mensagem': 'M', 'honeypot': ''}
        
        client.post(url, data, follow=True) # Primeiro envio: Sucesso
        response = client.post(url, data, follow=True) # Segundo envio: Bloqueio
        
        conteudo = response.content.decode('utf-8')
        assert "recentemente" in conteudo or "aguarde" in conteudo

    def test_contato_honeypot_bot_protection(self, client):
        """ 
        Simula um robô preenchendo o campo 'honeypot' (que deveria estar vazio).
        O sistema deve ignorar o envio e não salvar nada no banco. 
        """
        url = reverse('home')
        data = {
            'nome': 'Bot', 'email': 'b@b.com', 'assunto': 'S', 
            'mensagem': 'A', 'honeypot': 'Sou robô'
        }
        response = client.post(url, data)
        assert response.status_code == 302 # Redirecionamento (Ignorado)
        assert MensagemContato.objects.count() == 0 # Nada foi salvo