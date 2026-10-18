"""
Testes das correções de interface da auditoria — spec 004, RF-01 a RF-24.

Cobre o HTML renderizado da home (cliente de teste do Django), as respostas da
view de contato, as páginas de erro e as regras que só existem em arquivo
estático: o CSS e o JavaScript são lidos como texto e conferidos por regra
(contraste calculado dos tokens, blocos ``@media``, marcadores de comportamento).
O navegador real (axe-core, Tab, medidas do hero) foi usado na auditoria e fica
fora do pytest.

Estratégia de isolamento: nenhuma chamada de rede. ``settings.EMAIL_BACKEND``
vai para o backend em memória e ``EMAIL_HOST_USER`` ganha um valor de teste, para
nenhum POST do formulário tentar o SMTP real do Gmail com a credencial do
``.env`` de quem roda a suíte. ``MEDIA_ROOT`` aponta para uma pasta temporária
(upload de currículo e de imagens), o cache é limpo a cada teste (rate limit por
IP) e ``SECURE_SSL_REDIRECT`` fica desligado. A falha de SMTP é simulada com
``send_mail`` mockado no ponto de uso (``app_portfolio.views``).
"""

import io
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.staticfiles import finders
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse
from django.views.defaults import permission_denied, server_error
from PIL import Image

from app_portfolio.models import (
    CategoriaHabilidade,
    CategoriaProjeto,
    Habilidade,
    Perfil,
    Projeto,
)
from app_portfolio.views import (
    MENSAGEM_DADOS_INVALIDOS,
    MENSAGEM_ENVIADO,
    MENSAGEM_FALHA_ENVIO,
    MENSAGEM_LIMITE_ENVIO,
)

RAIZ = Path(__file__).resolve().parent.parent

# Lidos uma vez como texto: a quebra de linha CRLF do Windows vira LF aqui.
CSS = (RAIZ / "static/css/styles.css").read_text(encoding="utf-8")
JS = (RAIZ / "static/js/main.js").read_text(encoding="utf-8")

# Mesmo piso do CSS para texto normal (WCAG 2.2, critério 1.4.3)
CONTRASTE_MINIMO = 4.5

# Corpo mínimo de um envio válido do formulário de contato
ENVIO_VALIDO = {
    "nome": "Visitante",
    "email": "visitante@example.com",
    "assunto": "Oi",
    "mensagem": "Mensagem de teste",
    "honeypot": "",
}
AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


# ---------------------------------------------------------------------------
# Fixtures e auxiliares
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def ambiente_isolado(settings, tmp_path) -> None:
    """Isola e-mail, mídia, cache e redirecionamento HTTPS de cada teste."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.EMAIL_HOST_USER = "contato-teste@example.com"
    settings.MEDIA_ROOT = str(tmp_path)
    settings.SECURE_SSL_REDIRECT = False
    cache.clear()  # isola o rate limit por IP entre os testes


def _perfil(**campos) -> Perfil:
    """
    Cria o perfil da home com valores de teste.

    Args:
        **campos (dict): Campos do ``Perfil`` que substituem os padrões.

    Returns:
        Perfil: Perfil salvo, sem foto e sem currículo (ambos opcionais).
    """
    padrao = {"nome": "Ana Dev", "cargo": "Desenvolvedora"}
    return Perfil.objects.create(**{**padrao, **campos})


def _home(client) -> str:
    """
    Baixa a home e devolve o HTML.

    Args:
        client (django.test.Client): Cliente de teste do Django.

    Returns:
        str: Corpo da resposta decodificado em UTF-8.
    """
    resposta = client.get(reverse("home"))
    assert resposta.status_code == 200
    return str(resposta.content.decode("utf-8"))  # str(): o mypy vê Any no client


def _bloco(texto: str, cabecalho: str) -> str:
    """
    Extrai o conteúdo de um bloco ``{ ... }`` a partir do seu cabeçalho.

    Args:
        texto (str): CSS completo.
        cabecalho (str): Texto que abre o bloco, ex.: ``"@media (max-width: 640px)"``.

    Returns:
        str: O que está entre as chaves do bloco, com as chaves internas casadas.
    """
    inicio = texto.index(cabecalho)
    abre = texto.index("{", inicio)
    profundidade = 0
    for posicao in range(abre, len(texto)):
        if texto[posicao] == "{":
            profundidade += 1
        elif texto[posicao] == "}":
            profundidade -= 1
            if profundidade == 0:
                return texto[abre + 1 : posicao]
    raise AssertionError(f"bloco sem fechamento: {cabecalho}")


def _regra(texto: str, seletor: str) -> str:
    """
    Devolve as declarações da primeira regra cujo seletor é exatamente ``seletor``.

    Args:
        texto (str): CSS (ou o conteúdo de um bloco ``@media``).
        seletor (str): Seletor completo, ex.: ``".hero__stats"``.

    Returns:
        str: Texto entre as chaves da regra.
    """
    achado = re.search(rf"(?m)^\s*{re.escape(seletor)}\s*\{{([^}}]*)\}}", texto)
    assert achado, f"regra não encontrada: {seletor}"
    return achado.group(1)


def _tokens() -> dict[str, str]:
    """
    Lê as cores ``--color-*`` hexadecimais do ``:root`` do CSS.

    Returns:
        dict[str, str]: Nome do token (sem ``--``) para o valor ``#rrggbb``.
    """
    raiz = _bloco(CSS, ":root")
    return dict(re.findall(r"--(color-[a-z0-9-]+):\s*(#[0-9a-fA-F]{6})", raiz))


def _luminancia(cor: str) -> float:
    """
    Calcula a luminância relativa de uma cor ``#rrggbb`` (WCAG).

    Args:
        cor (str): Cor hexadecimal com ``#``.

    Returns:
        float: Luminância entre 0 (preto) e 1 (branco).
    """
    canais = [int(cor[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lineares = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais
    ]
    return 0.2126 * lineares[0] + 0.7152 * lineares[1] + 0.0722 * lineares[2]


def _contraste(frente: str, fundo: str) -> float:
    """
    Calcula a razão de contraste WCAG entre duas cores.

    Args:
        frente (str): Cor do texto, ``#rrggbb``.
        fundo (str): Cor do fundo, ``#rrggbb``.

    Returns:
        float: Razão de 1 a 21.
    """
    claro, escuro = sorted((_luminancia(frente), _luminancia(fundo)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


# ---------------------------------------------------------------------------
# RF-01 — Home sem currículo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCurriculoOpcional:
    def test_home_sem_curriculo_responde_200(self, client) -> None:
        """Perfil sem PDF não derruba a home com ValueError (antes: erro 500)."""
        _perfil()
        html = _home(client)
        assert "Download CV" not in html

    def test_home_com_curriculo_mostra_o_botao(self, client) -> None:
        """Com o PDF anexado, o botão aparece e aponta para o arquivo."""
        arquivo = SimpleUploadedFile("cv.pdf", b"%PDF-1.4", "application/pdf")
        _perfil(curriculo=arquivo)
        html = _home(client)
        assert "Download CV" in html
        assert "/media/curriculo/cv" in html


# ---------------------------------------------------------------------------
# RF-02 — O hero cabe na primeira tela do celular
# ---------------------------------------------------------------------------


class TestHeroNoCelular:
    def test_bloco_de_codigo_nao_vai_para_o_topo(self) -> None:
        """O CSS não usa mais order: -1 no .hero__visual (empurrava o texto)."""
        assert "order: -1" not in CSS

    def test_bloco_de_codigo_some_no_celular(self) -> None:
        """Até 640 px o bloco decorativo é escondido."""
        bloco = _bloco(CSS, "@media (max-width: 640px) {\n    .hero__visual")
        assert "display: none" in _regra(bloco, ".hero__visual")

    def test_bloco_de_codigo_some_no_celular_deitado(self) -> None:
        """Em tela baixa e deitada (~340 px de altura) o bloco também sai."""
        bloco = _bloco(CSS, "@media (max-height: 500px) and (orientation: landscape)")
        assert "display: none" in _regra(bloco, ".hero__visual")

    def test_estatisticas_ficam_numa_linha(self) -> None:
        """As três estatísticas formam uma grade de 3 colunas, não 2 + 1."""
        bloco = _bloco(CSS, "@media (max-width: 1024px) {\n    .hero__scroll")
        regra = _regra(bloco, ".hero__stats")
        assert "grid-template-columns: repeat(3, 1fr)" in regra

    def test_altura_do_hero_usa_svh(self) -> None:
        """O hero usa 100svh (altura com a barra do navegador visível)."""
        assert "min-height: 100svh" in _regra(CSS, ".hero")


# ---------------------------------------------------------------------------
# RF-03 — O visitante vê o resultado do envio
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFeedbackDoFormulario:
    def test_limite_de_envio_devolve_a_frase_completa_em_json(self, client) -> None:
        """O 429 traz a mensagem completa (antes: "Muitas tentativas...")."""
        url = reverse("home")
        client.post(url, ENVIO_VALIDO, **AJAX)
        resposta = client.post(url, ENVIO_VALIDO, **AJAX)
        assert resposta.status_code == 429
        assert resposta.json()["message"] == MENSAGEM_LIMITE_ENVIO
        assert "..." not in resposta.json()["message"]

    def test_dados_invalidos_devolvem_mensagem_em_json(self, client) -> None:
        """O 400 explica o que fazer, não só "Dados inválidos."."""
        resposta = client.post(
            reverse("home"), {**ENVIO_VALIDO, "email": "nao-e-email"}, **AJAX
        )
        assert resposta.status_code == 400
        assert resposta.json()["message"] == MENSAGEM_DADOS_INVALIDOS

    def test_falha_de_smtp_devolve_mensagem_em_json(self, client) -> None:
        """O 500 por falha de e-mail traz a frase para o visitante."""
        with patch("app_portfolio.views.send_mail", side_effect=Exception("SMTP")):
            resposta = client.post(reverse("home"), ENVIO_VALIDO, **AJAX)
        assert resposta.status_code == 500
        assert resposta.json()["message"] == MENSAGEM_FALHA_ENVIO

    def test_envio_html_valido_mostra_aviso_de_sucesso(self, client) -> None:
        """Sem JavaScript, o redirect leva um aviso de sucesso visível."""
        resposta = client.post(reverse("home"), ENVIO_VALIDO, follow=True)
        html = resposta.content.decode("utf-8")
        assert "notification notification--success" in html
        assert MENSAGEM_ENVIADO in html

    def test_envio_html_barrado_mostra_o_limite(self, client) -> None:
        """Sem JavaScript, o segundo envio mostra o aviso de limite."""
        url = reverse("home")
        client.post(url, ENVIO_VALIDO, follow=True)
        html = client.post(url, ENVIO_VALIDO, follow=True).content.decode("utf-8")
        assert "notification notification--error" in html
        assert MENSAGEM_LIMITE_ENVIO in html

    def test_envio_html_invalido_mostra_aviso(self, client) -> None:
        """Sem JavaScript, o formulário inválido volta com um aviso de erro."""
        resposta = client.post(reverse("home"), {**ENVIO_VALIDO, "email": "x"})
        html = resposta.content.decode("utf-8")
        assert MENSAGEM_DADOS_INVALIDOS in html
        assert "notification--error" in html

    def test_envio_html_com_falha_de_smtp_mostra_aviso(self, client) -> None:
        """Sem JavaScript, a falha de e-mail também avisa o visitante."""
        with patch("app_portfolio.views.send_mail", side_effect=Exception("SMTP")):
            resposta = client.post(reverse("home"), ENVIO_VALIDO)
        assert MENSAGEM_FALHA_ENVIO in resposta.content.decode("utf-8")

    def test_javascript_trata_toda_resposta_que_nao_e_sucesso(self) -> None:
        """O main.js tem o ramo de erro com a mensagem do servidor (antes só success)."""
        assert "resposta.ok" in JS
        assert re.search(r"\}\s*else\s*\{\s*mostrarNotificacao\(", JS)
        assert "dados.message" in JS


# ---------------------------------------------------------------------------
# RF-04 — Menu do celular e foco por teclado
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMenuDoCelular:
    def test_botao_do_menu_declara_o_estado(self, client) -> None:
        """O hambúrguer nasce com aria-expanded="false" e aponta para o painel."""
        _perfil()
        html = _home(client)
        botao = re.search(r'<button[^>]*id="nav-toggle"[^>]*>', html)
        assert botao
        assert 'aria-expanded="false"' in botao.group(0)
        assert 'aria-controls="nav-menu"' in botao.group(0)

    def test_javascript_bloqueia_o_painel_fechado(self) -> None:
        """O painel é inert fechado (no celular) e o foco vai e volta ao abrir e fechar."""
        assert "const bloqueado = MENU_DE_CELULAR.matches && !menuEstaAberto();" in JS
        assert "navMenu.inert = bloqueado;" in JS
        assert "matchMedia('(max-width: 768px)')" in JS
        assert "setAttribute('aria-expanded', 'true')" in JS
        assert "devolverFoco" in JS
        assert "e.key === 'Escape'" in JS

    def test_javascript_devolve_o_foco_antes_do_inert(self) -> None:
        """O foco volta ao botão ANTES do painel virar inert (senão cai no body)."""
        # Fatia até a função seguinte: o cabeçalho de fecharMenu() tem chaves
        # (parâmetro desestruturado) que atrapalhariam o _bloco().
        corpo = JS[JS.index("function fecharMenu(") : JS.index("function iniciarMenu(")]
        assert corpo.index("navToggle.focus()") < corpo.index("sincronizarMenu()")

    def test_corte_do_menu_bate_com_o_css(self) -> None:
        """O ponto de corte do JavaScript é o mesmo do @media do menu."""
        assert "@media (max-width: 768px) {\n    .nav__menu" in CSS

    def test_ha_anel_de_foco_para_teclado(self) -> None:
        """Existe regra :focus-visible, e o JS não alterna mais .keyboard-nav."""
        assert "outline: 2px solid var(--color-accent)" in _regra(CSS, ":focus-visible")
        assert "keyboard-nav" not in JS

    def test_outline_none_so_nos_campos_com_anel_proprio(self) -> None:
        """O único outline: none é o do campo, que troca por borda e sombra."""
        regra = _regra(CSS, ".form__input:focus,\n.form__textarea:focus")
        assert "outline: none" in regra and "box-shadow" in regra
        assert CSS.count("outline: none") == 1


# ---------------------------------------------------------------------------
# RF-05 — Contraste do texto
# ---------------------------------------------------------------------------


class TestContraste:
    def test_texto_de_apoio_passa_em_todos_os_fundos(self) -> None:
        """--color-gray-400 tem 4,5:1 ou mais sobre os quatro fundos escuros."""
        cores = _tokens()
        for fundo in (
            "color-bg-primary",
            "color-bg-secondary",
            "color-bg-tertiary",
            "color-bg-card",
        ):
            razao = _contraste(cores["color-gray-400"], cores[fundo])
            assert razao >= CONTRASTE_MINIMO, (fundo, round(razao, 2))

    def test_copyright_e_placeholder_usam_o_token_legivel(self) -> None:
        """O copyright (era 2,18:1) e o texto de exemplo dos campos usam gray-400."""
        assert "var(--color-gray-400)" in _regra(CSS, ".footer__copyright")
        placeholder = _regra(
            CSS, ".form__input::placeholder,\n.form__textarea::placeholder"
        )
        assert "var(--color-gray-400)" in placeholder

    def test_nenhum_texto_usa_o_token_gray_500(self) -> None:
        """gray-500 (2,2:1) só serve de borda: nenhuma regra de cor de texto o usa."""
        usos = re.findall(r"(?m)^\s*color:\s*var\(--color-gray-500\)", CSS)
        assert usos == []


# ---------------------------------------------------------------------------
# RF-06 — Avisos acessíveis
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAvisos:
    def test_texto_branco_passa_em_cada_tipo_de_aviso(self) -> None:
        """Texto claro sobre sucesso, erro e informação tem 4,5:1 ou mais."""
        cores = _tokens()
        for fundo in ("color-success", "color-error", "color-info"):
            razao = _contraste(cores["color-white"], cores[fundo])
            assert razao >= CONTRASTE_MINIMO, (fundo, round(razao, 2))

    def test_javascript_nao_define_cores_nem_estilo_do_aviso(self) -> None:
        """As cores saíram do JS: o visual do aviso mora no CSS."""
        assert "style.cssText" not in JS
        assert "#10b981" not in JS and "#ef4444" not in JS

    def test_aviso_de_erro_e_anunciado_e_fechavel(self) -> None:
        """O erro leva role=alert; o botão de fechar tem nome e o contêiner é role=status."""
        assert "'role', 'alert'" in JS
        assert "'aria-label', 'Fechar aviso'" in JS
        assert "'role', 'status'" in JS

    def test_botao_de_fechar_tem_44_px(self) -> None:
        """A área do × tem 2,75rem (44 px); antes eram 9 x 16 px."""
        regra = _regra(CSS, ".notification__close")
        assert "width: 2.75rem" in regra and "height: 2.75rem" in regra

    def test_aviso_de_erro_do_servidor_e_uma_regiao_viva(self, client) -> None:
        """No fluxo HTML o aviso vem dentro de uma região role=status."""
        html = client.post(reverse("home"), {**ENVIO_VALIDO, "email": "x"}).content
        assert 'class="notifications" role="status"' in html.decode("utf-8")


# ---------------------------------------------------------------------------
# RF-07 — Barras de habilidade com nome
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_barra_de_progresso_tem_nome(client) -> None:
    """Cada role=progressbar leva aria-label com a habilidade."""
    _perfil(mostrar_progresso=True)
    categoria = CategoriaHabilidade.objects.create(nome="Backend")
    Habilidade.objects.create(categoria=categoria, nome="Python", progresso=90)
    html = _home(client)
    barra = re.search(r'<div[^>]*role="progressbar"[^>]*>', html)
    assert barra
    assert 'aria-label="Python"' in barra.group(0)


# ---------------------------------------------------------------------------
# RF-08 — Movimento reduzido
# ---------------------------------------------------------------------------


class TestMovimentoReduzido:
    def test_css_tem_o_bloco_de_movimento_reduzido(self) -> None:
        """O bloco prefers-reduced-motion desliga rolagem suave e animações contínuas."""
        bloco = _bloco(CSS, "@media (prefers-reduced-motion: reduce)")
        assert "scroll-behavior: auto" in bloco
        assert "animation: none" in _regra(
            bloco, ".hero__visual,\n    .scroll-indicator"
        )
        assert "opacity: 1" in _regra(bloco, ".reveal")

    def test_bloco_de_movimento_reduzido_e_o_ultimo_do_arquivo(self) -> None:
        """Vem por último para vencer as regras de hover e de animação acima."""
        assert CSS.rindex("@media (prefers-reduced-motion: reduce)") > CSS.rindex(
            "@keyframes"
        )
        assert CSS.rindex("@media (prefers-reduced-motion: reduce)") > CSS.rindex(
            "@media (pointer: coarse)"
        )

    def test_rolagem_do_javascript_pergunta_o_criterio(self) -> None:
        """Nenhum behavior: 'smooth' fixo; tudo passa por comportamentoDeRolagem()."""
        assert "(prefers-reduced-motion: reduce)" in JS
        assert "behavior: 'smooth'" not in JS
        assert "behavior: comportamentoDeRolagem()" in JS


# ---------------------------------------------------------------------------
# RF-09 — Foto padrão do perfil
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_foto_padrao_do_perfil_existe(client) -> None:
    """Sem foto, o template aponta para um arquivo que existe (antes: 404)."""
    _perfil()
    html = _home(client)
    assert "icons/default_perfil.webp" in html
    assert "avatar_padrao" not in html
    assert finders.find("icons/default_perfil.webp")


class TestImagensPadrao:
    def test_foto_padrao_tem_a_proporcao_da_tela(self) -> None:
        """A foto de reserva é 4:5, a proporção do .about__image (antes: 928 x 1152)."""
        imagem = Image.open(RAIZ / "static/icons/default_perfil.webp")
        assert imagem.width * 5 == imagem.height * 4

    def test_capa_padrao_tem_a_proporcao_do_cartao(self) -> None:
        """A capa de reserva é 16:10, a do .project-card__image (antes: 1408 x 768)."""
        imagem = Image.open(RAIZ / "static/icons/default_projeto.webp")
        assert imagem.width * 10 == imagem.height * 16

    def test_imagens_padrao_sao_leves(self) -> None:
        """As duas pesam menos de 150 KiB (a capa tinha 622 KiB, com texto desenhado)."""
        for nome in ("default_perfil.webp", "default_projeto.webp"):
            assert (RAIZ / "static/icons" / nome).stat().st_size < 150 * 1024


# ---------------------------------------------------------------------------
# RF-10 — Link do GitHub opcional e com nome próprio
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLinkDoProjeto:
    def test_projeto_sem_link_nao_gera_href_none(self, client) -> None:
        """Sem repositório, o botão some e não sobra href="None"."""
        _perfil()
        Projeto.objects.create(titulo="Sem Repo", descricao="Descrição")
        html = _home(client)
        assert 'href="None"' not in html
        assert "btn-github" not in html

    def test_cada_link_tem_nome_proprio(self, client) -> None:
        """O link ganha o nome do projeto para o leitor de tela."""
        _perfil()
        Projeto.objects.create(
            titulo="Loja", descricao="Descrição", link_github="https://github.com/a/b"
        )
        html = _home(client)
        assert 'Ver no GitHub<span class="sr-only"> do projeto Loja</span>' in html


# ---------------------------------------------------------------------------
# RF-11 — O nome acessível começa pelo texto visível
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nomes_acessiveis_comecam_pelo_texto_visivel(client) -> None:
    """O logo e o "Explorar" têm aria-label que contém o texto que aparece."""
    _perfil(nome="Ana Dev")
    html = _home(client)
    assert 'aria-label="Ana Dev, voltar ao início"' in html
    assert 'aria-label="Explorar: rolar para a seção Sobre"' in html


# ---------------------------------------------------------------------------
# RF-12 — Títulos sem pulo de nível
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_rodape_nao_usa_h4(client) -> None:
    """Os títulos do rodapé são h2 (antes h4 logo depois de h2)."""
    _perfil(link_github="https://github.com/ana")
    html = _home(client)
    assert "<h4" not in html
    assert html.count('<h2 class="footer__title">') == 2


# ---------------------------------------------------------------------------
# RF-13 — Filtros com estado e campos com autocomplete
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFiltrosECampos:
    def test_filtros_declaram_aria_pressed(self, client) -> None:
        """ "Todos" nasce pressionado; os demais, não."""
        _perfil()
        CategoriaProjeto.objects.create(nome="Web", slug="web")
        html = _home(client)
        assert re.search(r'data-filter="all"[^>]*aria-pressed="true"', html)
        assert re.search(r'data-filter="web"[^>]*aria-pressed="false"', html)
        assert 'id="projects-status"' in html

    def test_javascript_atualiza_o_estado_e_o_anuncio(self) -> None:
        """O JS alterna aria-pressed e escreve a contagem na região viva."""
        assert "setAttribute('aria-pressed', 'true')" in JS
        assert "projectsStatus.textContent" in JS

    def test_campos_pedem_preenchimento_automatico(self, client) -> None:
        """Nome e e-mail declaram o autocomplete certo (WCAG 1.3.5)."""
        _perfil()
        html = _home(client)
        assert re.search(r'name="nome"[^>]*autocomplete="name"', html)
        assert re.search(r'name="email"[^>]*autocomplete="email"', html)


# ---------------------------------------------------------------------------
# RF-14 — Sem texto provisório: o contato sai do perfil; o rodapé é fixo
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestContatoERodape:
    def test_texto_do_link_sai_do_endereco_do_perfil(self, client) -> None:
        """O cartão mostra o endereço do perfil, não "/in/seu_usuario"."""
        _perfil(
            link_linkedin="https://www.linkedin.com/in/ana",
            link_github="https://github.com/ana",
        )
        html = _home(client)
        assert ">linkedin.com/in/ana</a>" in html
        assert ">github.com/ana</a>" in html
        assert "seu_usuario" not in html

    def test_links_externos_do_contato_tem_noopener(self, client) -> None:
        """Os dois links do contato com target=_blank levam rel=noopener."""
        _perfil(
            link_linkedin="https://www.linkedin.com/in/a",
            link_github="https://github.com/a",
        )
        html = _home(client)
        for tag in re.findall(r'<a [^>]*class="contact__card-link"[^>]*>', html):
            if 'target="_blank"' in tag:
                assert 'rel="noopener"' in tag

    def test_cartao_do_contato_some_sem_o_link(self, client) -> None:
        """Perfil sem LinkedIn não mostra o cartão do LinkedIn."""
        _perfil()
        assert 'contact__card-title">LinkedIn' not in _home(client)

    def test_rodape_tem_as_seis_redes_fixas(self, client) -> None:
        """O rodapé é fixo: as seis redes aparecem mesmo com o perfil vazio."""
        _perfil()
        html = _home(client)
        for rede in ("Facebook", "Instagram", "LinkedIn", "X", "TikTok", "GitHub"):
            assert f'aria-label="{rede}"' in html
        assert "Redes Sociais" in html

    def test_redes_do_rodape_nao_dependem_do_perfil(self, client) -> None:
        """Preencher LinkedIn e GitHub no perfil não muda os links do rodapé."""
        _perfil(
            link_linkedin="https://www.linkedin.com/in/ana",
            link_github="https://github.com/ana",
        )
        html = _home(client)
        rodape = html[html.index('<div class="footer__social">') :]
        assert 'href="https://www.linkedin.com/in/"' in rodape
        assert 'href="https://github.com/"' in rodape
        assert "linkedin.com/in/ana" not in rodape

    def test_perfil_nao_tem_campos_de_rede_do_rodape(self) -> None:
        """Os campos que o rodapé dinâmico usava não existem mais no modelo."""
        nomes = {campo.name for campo in Perfil._meta.get_fields()}
        assert not nomes & {"link_instagram", "link_facebook", "link_x", "link_tiktok"}

    def test_logo_do_rodape_leva_ao_topo(self, client) -> None:
        """O logo do rodapé aponta para #home, não para href="#"."""
        _perfil()
        assert 'href="#"' not in _home(client)


# ---------------------------------------------------------------------------
# RF-15 — Transições listadas e altura dinâmica
# ---------------------------------------------------------------------------


class TestTransicoesEAltura:
    def test_nenhuma_transicao_all(self) -> None:
        """Toda transição lista as propriedades (antes: 12 transition: all)."""
        assert "transition: all" not in CSS

    def test_menu_e_hero_usam_unidades_dinamicas(self) -> None:
        """O painel do menu usa 100dvh e o hero 100svh, com 100vh de reserva."""
        menu = _bloco(CSS, "@media (max-width: 768px) {\n    .nav__menu")
        regra = _regra(menu, ".nav__menu")
        assert regra.index("height: 100vh") < regra.index("height: 100dvh")


# ---------------------------------------------------------------------------
# RF-16 — Botões com a mesma altura
# ---------------------------------------------------------------------------


class TestAlturaDosBotoes:
    def test_botao_base_tem_borda_transparente(self) -> None:
        """.btn tem borda de 2px, então o primário e o secundário medem igual."""
        assert "border: 2px solid transparent" in _regra(CSS, ".btn")

    def test_secundario_so_troca_a_cor_da_borda(self) -> None:
        """.btn--secondary não redefine a espessura (usa border-color)."""
        regra = _regra(CSS, ".btn--secondary")
        assert "border-color" in regra
        assert "border: 2px" not in regra


# ---------------------------------------------------------------------------
# RF-17 — Fontes hospedadas no projeto
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFontesLocais:
    def test_pagina_nao_chama_o_google_fonts(self, client) -> None:
        """Nenhuma referência ao Google Fonts no HTML nem no CSS."""
        _perfil()
        html = _home(client)
        fontes_css = (RAIZ / "static/css/fontes.css").read_text(encoding="utf-8")
        for texto in (html, CSS, fontes_css):
            assert "fonts.googleapis.com" not in texto
            assert "fonts.gstatic.com" not in texto

    def test_arquivos_de_fonte_e_licencas_existem(self) -> None:
        """Cada @font-face aponta para um arquivo que existe, com a licença OFL ao lado."""
        fontes_css = (RAIZ / "static/css/fontes.css").read_text(encoding="utf-8")
        arquivos = re.findall(r"url\('\.\./fonts/([^']+)'\)", fontes_css)
        assert len(arquivos) == 2
        for nome in arquivos:
            assert (RAIZ / "static/fonts" / nome).is_file()
        assert (RAIZ / "static/fonts/OFL-inter.txt").is_file()
        assert (RAIZ / "static/fonts/OFL-jetbrains-mono.txt").is_file()

    def test_font_face_usa_swap(self) -> None:
        """Os dois @font-face usam font-display: swap (texto visível enquanto carrega)."""
        fontes_css = (RAIZ / "static/css/fontes.css").read_text(encoding="utf-8")
        assert fontes_css.count("font-display: swap;") == 2

    def test_home_carrega_fontes_css_e_faz_preload_da_inter(self, client) -> None:
        """O <head> traz o fontes.css e o preload do arquivo da Inter."""
        _perfil()
        html = _home(client)
        assert "css/fontes.css" in html
        assert 'rel="preload"' in html and "inter-latin-variavel.woff2" in html

    def test_csp_nao_libera_mais_o_google(self, settings) -> None:
        """Os hosts do Google saíram de style-src e font-src."""
        assert all(
            "google" not in h and "gstatic" not in h for h in settings.CSP_STYLE_SRC
        )
        assert all(
            "google" not in h and "gstatic" not in h for h in settings.CSP_FONT_SRC
        )


# ---------------------------------------------------------------------------
# RF-18 — Alvos de toque
# ---------------------------------------------------------------------------


class TestAlvosDeToque:
    def test_controles_pequenos_chegam_a_44_px_em_tela_de_toque(self) -> None:
        """Com pointer: coarse, filtros e links do rodapé e do contato têm 44 px."""
        bloco = _bloco(CSS, "@media (pointer: coarse)")
        assert "min-height: 2.75rem" in _regra(bloco, ".filter-btn")
        assert "min-height: 2.75rem" in _regra(bloco, ".footer__link")
        assert "padding-block: 0.75rem" in _regra(bloco, ".contact__card-link")
        assert "width: 2.75rem" in _regra(bloco, ".social__link")

    def test_botoes_do_menu_do_celular_tem_44_px(self) -> None:
        """O hambúrguer e o fechar têm 2,75rem; os links do painel, padding vertical."""
        menu = _bloco(CSS, "@media (max-width: 768px) {\n    .nav__menu")
        assert "width: 2.75rem" in _regra(menu, ".nav__toggle,\n    .nav__close")
        assert "padding-block: 0.5rem" in _regra(menu, ".nav__link")


# ---------------------------------------------------------------------------
# RF-19 — Páginas de erro do projeto
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaginasDeErro:
    def test_404_usa_a_pagina_do_projeto(self, client) -> None:
        """Endereço inexistente mostra a página em português, não a do Django."""
        resposta = client.get("/nao-existe/")
        html = resposta.content.decode("utf-8")
        assert resposta.status_code == 404
        assert 'lang="pt-BR"' in html and "Página não encontrada" in html
        assert 'name="viewport"' in html and "<main" in html and html.count("<h1") == 1
        assert 'name="robots" content="noindex"' in html

    def test_403_usa_a_pagina_do_projeto(self) -> None:
        """O handler de 403 renderiza o 403.html do projeto."""
        resposta = permission_denied(RequestFactory().get("/"), Exception())
        html = resposta.content.decode("utf-8")
        assert resposta.status_code == 403
        assert "Ação não permitida" in html and 'lang="pt-BR"' in html

    def test_500_nao_toca_no_banco(self, django_assert_num_queries) -> None:
        """O 500 é renderizado sem consulta ao banco, sessão ou contexto."""
        with django_assert_num_queries(0):
            resposta = server_error(RequestFactory().get("/"))
        html = resposta.content.decode("utf-8")
        assert resposta.status_code == 500
        assert "Algo deu errado" in html and "Voltar para a página inicial" in html

    def test_paginas_de_erro_nao_tem_javascript_nem_base(self) -> None:
        """O erro.html é independente: não herda o base.html e não carrega script."""
        texto = (RAIZ / "templates/erro.html").read_text(encoding="utf-8")
        assert "extends" not in texto and "<script" not in texto
        for nome in ("404", "403", "500"):
            filho = (RAIZ / f"templates/{nome}.html").read_text(encoding="utf-8")
            assert "{% extends 'erro.html' %}" in filho


# ---------------------------------------------------------------------------
# RF-20 — Imagem de compartilhamento e ícone da aba
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCompartilhamentoEIcone:
    def test_og_image_tem_endereco_absoluto(self, client) -> None:
        """A og:image sai com esquema e host, não só /media/..."""
        foto = SimpleUploadedFile("foto.webp", _webp_minimo(), "image/webp")
        _perfil(foto=foto)
        html = _home(client)
        achado = re.search(r'property="og:image" content="([^"]+)"', html)
        assert achado
        assert achado.group(1).startswith("http://testserver/media/perfil/")

    def test_favicon_declara_o_tipo_certo(self, client) -> None:
        """O <link rel=icon> diz image/webp para um arquivo .webp."""
        _perfil()
        html = _home(client)
        assert re.search(
            r'rel="icon" type="image/webp" href="[^"]*favicon\.webp"', html
        )

    def test_rota_do_favicon_ico_leva_a_um_arquivo_que_existe(self, client) -> None:
        """/favicon.ico redireciona para o favicon.webp (antes: favicon.png, 404)."""
        resposta = client.get("/favicon.ico")
        assert resposta.status_code == 302
        assert resposta["Location"] == "/static/icons/favicon.webp"
        assert finders.find("icons/favicon.webp")

    def test_favicon_e_leve_e_quadrado(self) -> None:
        """O ícone da aba é quadrado e pesa menos de 20 KiB (antes: 1024 x 1024, 516 KiB)."""
        arquivo = RAIZ / "static/icons/favicon.webp"
        assert arquivo.stat().st_size < 20 * 1024
        assert Image.open(arquivo).width == Image.open(arquivo).height <= 512


def _webp_minimo() -> bytes:
    """
    Gera um WebP 1x1 em memória para o upload da foto do perfil.

    Returns:
        bytes: Conteúdo de um arquivo ``.webp`` válido (o ``save()`` do model
            não reconverte WebP).
    """

    buffer = io.BytesIO()
    Image.new("RGB", (1, 1), "red").save(buffer, format="WEBP")
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# RF-21 — Texto alternativo das capas
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_capa_de_projeto_e_decorativa(client) -> None:
    """A capa tem alt vazio: o título ao lado já nomeia o projeto."""
    _perfil()
    Projeto.objects.create(titulo="Loja", descricao="Descrição")
    html = _home(client)
    capa = re.search(r'<img[^>]*class="project-card__img"[^>]*>', html, re.S)
    assert capa
    assert 'alt=""' in capa.group(0)
    assert "Thumbnail" not in html


# ---------------------------------------------------------------------------
# RF-22 — Sem código nem CSS sobrando
# ---------------------------------------------------------------------------


class TestSemCodigoSobrando:
    def test_css_sem_regras_de_classes_inexistentes(self) -> None:
        """As classes .project-card__overlay e __link não existem no HTML nem no CSS."""
        assert "project-card__overlay" not in CSS
        assert "project-card__link" not in CSS

    def test_javascript_sem_funcoes_desligadas(self) -> None:
        """Digitação, parallax, preloader e data-progress (que o template não gera) saíram."""
        for resto in ("data-progress", "initTypingEffect", "initParallax", "preloader"):
            assert resto not in JS


# ---------------------------------------------------------------------------
# RF-23 — Quebra de linha
# ---------------------------------------------------------------------------


def test_titulos_balanceados_e_paragrafos_sem_orfa() -> None:
    """text-wrap: balance nos títulos e pretty nos parágrafos e itens de lista."""
    assert "text-wrap: balance" in _regra(CSS, "h1,\nh2,\nh3,\nh4")
    assert "text-wrap: pretty" in _regra(CSS, "p,\nli")


# ---------------------------------------------------------------------------
# RF-24 — Rodapé alinhado e ícone legível
# ---------------------------------------------------------------------------


class TestRodapeEIcone:
    def test_colunas_do_rodape_alinham_pelo_topo(self) -> None:
        """As três colunas do rodapé começam na mesma altura."""
        assert "align-items: start" in _regra(CSS, ".footer__content")

    def test_icone_do_postgresql_aparece_sobre_o_chip_escuro(self) -> None:
        """O SVG usa um azul com 4,5:1 sobre o chip (o oficial dava 2,65:1)."""
        svg = (RAIZ / "static/icons/tech/postgresql.svg").read_text(encoding="utf-8")
        cor = re.search(r'fill="(#[0-9a-fA-F]{6})"', svg)
        assert cor
        chip = _tokens()["color-bg-tertiary"]
        assert _contraste(cor.group(1), chip) >= CONTRASTE_MINIMO
