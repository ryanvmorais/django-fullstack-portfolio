"""
🧪 PROJETO: TESTES DO README EM INGLÊS
🎯 Objetivo: Garantir que o ``README.en.md`` acompanhe a estrutura do ``README.md``.

O README em inglês é uma tradução, e tradução envelhece: uma seção nova no
``README.md`` que ninguém leva para o outro arquivo deixa o leitor estrangeiro com um
projeto mais antigo do que o do repositório. Os testes comparam a estrutura, nunca o
texto: a ordem dos títulos, as linhas da tabela de tecnologias, os selos do topo, os
blocos de comando, os links de troca entre os dois arquivos e os arquivos do
repositório para onde os links do inglês apontam.

Estratégia de isolamento: só os dois READMEs e a existência dos arquivos que eles
linkam são lidos, nada é mockado; numa árvore sem os dois arquivos, os testes são
pulados.
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# A raiz do repositório, um nível acima da pasta do app.
_RAIZ = Path(__file__).resolve().parents[1]
# Os dois arquivos comparados; sem um deles na árvore, os testes são pulados.
_PORTUGUES = _RAIZ / "README.md"
_INGLES = _RAIZ / "README.en.md"

# Alvo de um link ou imagem em Markdown: o texto entre "](" e o parêntese que fecha.
_ALVO = re.compile(r"\]\(([^)\s]+)\)")

# Título ATX; a sequência de "#" é o nível.
_TITULO = re.compile(r"^(#{1,6}) ")

# Selo do topo: ``![texto](URL)`` ou ``[![texto](URL)](link)``.
_SELO = re.compile(r"!\[[^\]]*\]\((https://img\.shields\.io/[^)]+|[^)]+badge\.svg)\)")

# Todos os testes precisam dos dois arquivos, então a marca é compartilhada.
_precisa_dos_dois = pytest.mark.skipif(
    not (_PORTUGUES.is_file() and _INGLES.is_file()),
    reason="os dois READMEs não estão nesta árvore",
)


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------


def _fora_dos_blocos(caminho: Path) -> list[str]:
    """
    Lê um arquivo Markdown e descarta as linhas dentro de blocos de código.

    Args:
        caminho (Path): O arquivo Markdown.

    Returns:
        list[str]: As linhas restantes, para que um comentário ``#`` num bloco de shell
            não seja contado como título.
    """
    mantidas: list[str] = []
    dentro = False
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if linha.lstrip().startswith("```"):
            dentro = not dentro
        elif not dentro:
            mantidas.append(linha)
    return mantidas


def _niveis(caminho: Path) -> list[int]:
    """
    Lista os níveis dos títulos de um README, na ordem.

    Args:
        caminho (Path): O arquivo Markdown.

    Returns:
        list[int]: Um nível (1 a 6) por título.
    """
    achados = (_TITULO.match(linha) for linha in _fora_dos_blocos(caminho))
    return [len(m.group(1)) for m in achados if m]


def _linhas_da_tabela(caminho: Path, primeira_celula: str) -> int:
    """
    Conta as linhas de dados da tabela cujo cabeçalho começa com uma célula.

    Args:
        caminho (Path): O arquivo Markdown.
        primeira_celula (str): O texto da primeira célula do cabeçalho.

    Returns:
        int: As linhas abaixo do cabeçalho, sem contar o cabeçalho e o separador.
    """
    linhas = _fora_dos_blocos(caminho)
    inicio = next(
        i for i, linha in enumerate(linhas) if linha.startswith(f"| {primeira_celula} ")
    )
    total = 0
    for linha in linhas[inicio + 2 :]:
        if not linha.startswith("|"):
            break
        total += 1
    return total


def _blocos_de_codigo(caminho: Path) -> list[str]:
    """
    Lista a linguagem de cada bloco de código cercado de um README, na ordem.

    Args:
        caminho (Path): O arquivo Markdown.

    Returns:
        list[str]: A linguagem de cada bloco que abre (``bash``, por exemplo).
    """
    abertura = re.compile(r"^\s*```(\w*)\s*$")
    linguagens: list[str] = []
    dentro = False
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        achou = abertura.match(linha)
        if achou and not dentro:
            linguagens.append(achou.group(1))
            dentro = True
        elif achou and dentro:
            dentro = False
    return linguagens


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


@_precisa_dos_dois
def test_os_dois_readmes_tem_os_mesmos_titulos_na_mesma_ordem() -> None:
    assert _niveis(_INGLES) == _niveis(_PORTUGUES)


@_precisa_dos_dois
def test_os_dois_readmes_tem_as_mesmas_tecnologias() -> None:
    assert _linhas_da_tabela(_INGLES, "Tool") == _linhas_da_tabela(
        _PORTUGUES, "Ferramenta"
    )


@_precisa_dos_dois
def test_os_dois_readmes_tem_os_mesmos_selos() -> None:
    # O rótulo do selo fica em inglês nos dois arquivos, então a lista é idêntica.
    texto_en = _INGLES.read_text(encoding="utf-8")
    texto_pt = _PORTUGUES.read_text(encoding="utf-8")

    assert _SELO.findall(texto_en) == _SELO.findall(texto_pt)
    assert _SELO.findall(texto_pt)


@_precisa_dos_dois
def test_os_dois_readmes_tem_os_mesmos_blocos_de_codigo() -> None:
    assert _blocos_de_codigo(_INGLES) == _blocos_de_codigo(_PORTUGUES)


@_precisa_dos_dois
def test_cada_readme_linka_o_outro_nas_primeiras_linhas() -> None:
    ingles = "\n".join(_fora_dos_blocos(_INGLES)[:5])
    portugues = "\n".join(_fora_dos_blocos(_PORTUGUES)[:5])

    assert "(README.md)" in ingles
    assert "(README.en.md)" in portugues


@_precisa_dos_dois
def test_os_links_do_readme_em_ingles_apontam_para_arquivos_do_repositorio() -> None:
    """Todo link relativo do README em inglês nomeia um arquivo que existe."""
    texto = _INGLES.read_text(encoding="utf-8")
    relativos = [
        alvo
        for alvo in _ALVO.findall(texto)
        if not alvo.startswith(("https://", "mailto:", "#"))
    ]

    ausentes = [alvo for alvo in relativos if not (_RAIZ / alvo.split("#")[0]).exists()]

    assert relativos
    assert ausentes == []


@_precisa_dos_dois
def test_as_ancoras_do_readme_em_ingles_existem_como_titulos() -> None:
    """Toda âncora ``#...`` do README em inglês corresponde a um título dele."""
    # A âncora do GitHub é o título em minúsculas, com hífen no lugar do espaço
    # e sem emoji.
    titulos = {
        re.sub(r"[^\w\- ]", "", linha.lstrip("# ").strip().lower(), flags=re.UNICODE)
        .strip()
        .replace(" ", "-")
        for linha in _fora_dos_blocos(_INGLES)
        if _TITULO.match(linha)
    }
    ancoras = [
        alvo[1:]
        for alvo in _ALVO.findall(_INGLES.read_text(encoding="utf-8"))
        if alvo.startswith("#")
    ]

    assert ancoras
    assert [a for a in ancoras if a not in titulos] == []
