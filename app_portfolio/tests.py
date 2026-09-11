"""
🧪 PROJETO: TESTES AUTOMATIZADOS (TESTS.PY)
🎯 Objetivo: Educacional - Validar a integridade, segurança e performance do sistema.

ESTRUTURA DO CÓDIGO:
1. FIXTURES: Configurações de ambiente para os testes (Limpeza, SSL, E-mail e Mídia).
2. TESTES DE CORE: Verificação de status code, criação de modelos e performance.
3. TESTES DE SEGURANÇA: Validação de XSS, Honeypot, Rate Limit e envio de e-mail.
4. TESTES DE UTILITÁRIOS: Conversão de imagem para WebP no save() dos models.

Estratégia de isolamento: nenhuma chamada de rede real é feita durante a
suíte, e nenhum teste depende do conteúdo do `.env` local. `settings.EMAIL_BACKEND`
é trocado para o backend em memória do Django e `settings.EMAIL_HOST_USER` é
fixado num valor de teste (`disable_real_email`, abaixo) — sem isso, os testes
que passam pelo fluxo de POST do formulário de contato disparariam
`send_mail()` contra o SMTP real do Gmail configurado em `settings.py` usando
a credencial real do `.env` de quem estiver rodando a suíte, tornando os
testes lentos, dependentes de rede, capazes de enviar e-mails de verdade, e
dependentes de uma variável de ambiente que não existe em CI. A falha de
envio (`test_contato_erro_envio_email`) mocka `views.send_mail` diretamente,
no ponto de uso.
"""

import io
from unittest.mock import patch

import pytest
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from app_portfolio.models import MensagemContato, Perfil, Projeto

# --- 1. CONFIGURAÇÕES DE AMBIENTE (FIXTURES) ---


@pytest.fixture(autouse=True)
def clear_cache():
    """Garante que o cache esteja limpo antes de cada teste de Rate Limit."""
    cache.clear()


@pytest.fixture(autouse=True)
def disable_ssl_redirect(settings):
    """
    Impedimos o redirecionamento HTTPS durante os testes para evitar
    erros de conexão no ambiente de teste controlado.
    """
    settings.SECURE_SSL_REDIRECT = False


@pytest.fixture(autouse=True)
def disable_real_email(settings):
    """
    Isola a suíte de qualquer credencial/estado de e-mail real.

    Troca `EMAIL_BACKEND` para o backend em memória do Django — sem isso,
    `views.home()` chamaria `send_mail()` contra o SMTP real do Gmail
    (host/porta fixos em `settings.py`) a cada POST de contato bem-sucedido.

    Também fixa `EMAIL_HOST_USER` num valor de teste: sem isso, a suíte
    herdaria o valor de `EMAIL_USER` do `.env` local (via `load_dotenv` em
    `settings.py`). Isso mascarava um bug — a suíte só passava na máquina de
    quem tinha um `.env` com credencial real preenchida, e falhava em CI (sem
    `.env`, `EMAIL_HOST_USER=None`), onde `send_mail()` com remetente/
    destinatário `None` não gera entrada em `mail.outbox`.
    """
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST_USER = "contato-teste@example.com"


@pytest.fixture(autouse=True)
def media_root_tmp(settings, tmp_path):
    """
    Redireciona MEDIA_ROOT para um diretório temporário durante os testes.

    Sem isso, os testes de upload de imagem (`TestConverterParaWebp`)
    gravariam arquivos reais na pasta `media/` do projeto a cada execução.
    """
    settings.MEDIA_ROOT = str(tmp_path)


def _uploaded_png(nome: str = "teste.png") -> SimpleUploadedFile:
    """
    Gera um PNG 1x1 válido em memória para testar upload de imagem.

    Evita depender de um arquivo fixture versionado no repositório.

    Args:
        nome (str, optional): Nome do arquivo simulado. Padrão: "teste.png".

    Returns:
        SimpleUploadedFile: Arquivo pronto para atribuir a um ImageField.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), color="red").save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(nome, buffer.read(), content_type="image/png")


# --- 2. TESTES DE CORE E PERFORMANCE ---


@pytest.mark.django_db  # Permite que o teste acesse o banco de dados
class TestPortfolioCore:
    def test_home_status_code(self, client) -> None:
        """Verifica se a página inicial está carregando (Status 200)."""
        url = reverse("home")
        response = client.get(url)
        assert response.status_code == 200

    def test_perfil_creation(self) -> None:
        """Valida se o modelo de Perfil está aceitando inserções corretamente."""
        Perfil.objects.create(nome="Dev Teste", cargo="Sênior")
        assert Perfil.objects.count() == 1

    def test_home_query_count(self, client, django_assert_max_num_queries) -> None:
        """
        TESTE SÊNIOR: Garante que a página inicial não ultrapasse 10 consultas ao banco.
        Isso previne lentidão causada pelo excesso de requisições (N+1).
        """
        with django_assert_max_num_queries(10):
            client.get(reverse("home"))


# --- 3. TESTES DE SEGURANÇA ---


@pytest.mark.django_db
class TestSegurancaContato:
    def test_contato_xss_sanitization(self, client) -> None:
        """
        Verifica se a sanitização (Bleach) está removendo tags maliciosas <script>
        antes de salvar a mensagem no banco de dados.
        """
        url = reverse("home")
        data = {
            "nome": "Hacker",
            "email": "hacker@evil.com",
            "assunto": "Ataque",
            "mensagem": '<script>alert("xss")</script>Olá',
            "honeypot": "",
        }
        client.post(url, data, follow=True)

        msg = MensagemContato.objects.last()
        assert msg is not None
        assert "<script>" not in msg.mensagem  # O script deve ter sido removido

    def test_rate_limit_blocking(self, client) -> None:
        """
        Valida o sistema de bloqueio. O primeiro envio deve passar,
        o segundo (imediato) deve retornar uma mensagem de erro/aguarde.
        """
        url = reverse("home")
        data = {
            "nome": "U",
            "email": "u@t.com",
            "assunto": "O",
            "mensagem": "M",
            "honeypot": "",
        }

        client.post(url, data, follow=True)  # Primeiro envio: Sucesso
        response = client.post(url, data, follow=True)  # Segundo envio: Bloqueio

        conteudo = response.content.decode("utf-8")
        assert "recentemente" in conteudo or "aguarde" in conteudo

    def test_contato_honeypot_bot_protection(self, client) -> None:
        """
        Simula um robô preenchendo o campo 'honeypot' (que deveria estar vazio).
        O sistema deve ignorar o envio e não salvar nada no banco.
        """
        url = reverse("home")
        data = {
            "nome": "Bot",
            "email": "b@b.com",
            "assunto": "S",
            "mensagem": "A",
            "honeypot": "Sou robô",
        }
        response = client.post(url, data)
        assert response.status_code == 302  # Redirecionamento (Ignorado)
        assert MensagemContato.objects.count() == 0  # Nada foi salvo

    def test_contato_envia_email_com_sucesso(self, client) -> None:
        """Um envio válido deve gerar exatamente um e-mail na caixa de saída."""
        url = reverse("home")
        data = {
            "nome": "U",
            "email": "u@t.com",
            "assunto": "O",
            "mensagem": "M",
            "honeypot": "",
        }

        client.post(url, data, follow=True)

        assert len(mail.outbox) == 1
        assert "O" in mail.outbox[0].subject

    def test_contato_ajax_sucesso_retorna_json(self, client) -> None:
        """Requisição AJAX bem-sucedida retorna JSON (não redirect) com status 200."""
        url = reverse("home")
        data = {
            "nome": "U",
            "email": "u@t.com",
            "assunto": "O",
            "mensagem": "M",
            "honeypot": "",
        }

        response = client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_contato_ajax_bloqueio_retorna_429(self, client) -> None:
        """Segundo envio AJAX dentro da janela de rate limit retorna HTTP 429."""
        url = reverse("home")
        data = {
            "nome": "U",
            "email": "u@t.com",
            "assunto": "O",
            "mensagem": "M",
            "honeypot": "",
        }
        headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

        client.post(url, data, **headers)
        response = client.post(url, data, **headers)

        assert response.status_code == 429

    def test_contato_erro_envio_email(self, client) -> None:
        """Falha no SMTP não derruba a request; AJAX recebe 500 com JSON de erro."""
        url = reverse("home")
        data = {
            "nome": "U",
            "email": "u@t.com",
            "assunto": "O",
            "mensagem": "M",
            "honeypot": "",
        }

        # Mockado no ponto de uso (app_portfolio.views), não em django.core.mail.
        with patch(
            "app_portfolio.views.send_mail", side_effect=Exception("SMTP indisponível")
        ):
            response = client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        assert response.status_code == 500
        assert response.json()["status"] == "error"

    def test_contato_ajax_dados_invalidos_retorna_400(self, client) -> None:
        """Formulário inválido (e-mail malformado) via AJAX retorna HTTP 400."""
        url = reverse("home")
        data = {
            "nome": "U",
            "email": "nao-e-email",
            "assunto": "O",
            "mensagem": "M",
            "honeypot": "",
        }

        response = client.post(url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        assert response.status_code == 400
        assert response.json()["status"] == "error"


# --- 4. TESTES DE UTILITÁRIOS (TRATAMENTO DE IMAGEM) ---


@pytest.mark.django_db
class TestConverterParaWebp:
    def test_save_converte_imagem_para_webp(self) -> None:
        """Upload de PNG é convertido para .webp na sobrescrita de save() do model."""
        projeto = Projeto.objects.create(
            titulo="Projeto Teste", descricao="Desc", imagem=_uploaded_png()
        )
        assert projeto.imagem.name.endswith(".webp")

    def test_save_sem_imagem_nao_falha(self) -> None:
        """Projeto sem imagem (campo opcional) salva normalmente, sem conversão."""
        projeto = Projeto.objects.create(titulo="Sem Imagem", descricao="Desc")
        assert not projeto.imagem
