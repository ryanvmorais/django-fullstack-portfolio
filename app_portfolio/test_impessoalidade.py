"""
🧪 PROJETO: TESTES DE IMPESSOALIDADE
🎯 Objetivo: Garantir que o que é versionado fale com quem clonou o repositório.

Tudo o que mora no repositório é escrito para quem o lê, e não para o mantenedor: o nome
dele não aparece em prosa, comentário ou nome de arquivo, e o ``CLAUDE.md`` descreve o
projeto sem apontar para skills pessoais, que quem clona não tem. Os testes varrem os
arquivos versionados e apontam o arquivo e a linha de cada violação.

Estratégia de isolamento: só a lista de arquivos do ``git ls-files`` e o texto deles são
lidos, nada é mockado; fora de uma árvore git, os testes são pulados.
"""

import re
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# A raiz do repositório, um nível acima da pasta do app.
_RAIZ = Path(__file__).resolve().parents[1]

# Arquivos em que o nome do mantenedor é legítimo: a licença (autoria) e este teste, que
# precisa citá-lo para procurá-lo.
_EXCECOES_NOME = frozenset({"LICENSE", "app_portfolio/test_impessoalidade.py"})

# O nome como palavra inteira, com maiúscula: as URLs do perfil (``ryanvmorais``) e o
# domínio de contato (``ryanmorais.com.br``) ficam de fora de propósito, por serem
# metadado público.
_NOME = re.compile(r"\bRyan\b")

# Skill pessoal citada como comando (``/idioma``, ``/spec``...). O lookbehind descarta
# caminhos como ``docs/stack.md``, onde a barra vem colada a outra palavra.
_SKILL_PESSOAL = re.compile(
    r"(?<![\w./-])/(idioma|spec|estilo-arquivos|fechar-sessao|atualizar-docs"
    r"|atualizar-dependencias|revisar-dependabot|nova-interface|stack|novo-projeto"
    r"|auditoria-interface|auditar-impessoalidade)\b"
)


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------


def _arquivos_versionados() -> list[str]:
    """
    Lista os arquivos versionados pelo git.

    Returns:
        list[str]: Os caminhos relativos à raiz, com barras ``/``; vazia se a raiz não
            for um repositório git ou se o git não estiver instalado.
    """
    try:
        saida = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=_RAIZ,
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    return [c for c in saida.decode("utf-8").split("\0") if c]


def _linhas(caminho: str) -> list[str]:
    """
    Lê as linhas de texto de um arquivo versionado.

    Args:
        caminho (str): O caminho relativo à raiz.

    Returns:
        list[str]: As linhas do arquivo; vazia se ele for binário (imagem, fonte) ou
            tiver sido apagado e ainda não removido do índice.
    """
    try:
        return (_RAIZ / caminho).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def _violacoes(
    caminhos: list[str], padrao: re.Pattern[str], excecoes: frozenset[str]
) -> list[str]:
    """
    Procura um padrão nas linhas de uma lista de arquivos.

    Args:
        caminhos (list[str]): Os arquivos a varrer.
        padrao (re.Pattern[str]): O que não pode aparecer.
        excecoes (frozenset[str]): Arquivos que o padrão pode citar.

    Returns:
        list[str]: Uma entrada ``arquivo:linha: trecho`` por ocorrência.
    """
    achadas: list[str] = []
    for caminho in caminhos:
        if caminho in excecoes:
            continue
        for numero, linha in enumerate(_linhas(caminho), start=1):
            if padrao.search(linha):
                achadas.append(f"{caminho}:{numero}: {linha.strip()[:100]}")
    return achadas


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def versionados() -> list[str]:
    """Os arquivos do git; pula o teste fora de uma árvore git."""
    arquivos = _arquivos_versionados()
    if not arquivos:
        pytest.skip("a raiz não é um repositório git")
    return arquivos


def test_nome_do_mantenedor_fora_dos_arquivos(versionados: list[str]) -> None:
    """Nenhum arquivo versionado cita o nome do mantenedor, salvo a licença."""
    achadas = _violacoes(versionados, _NOME, _EXCECOES_NOME)
    assert not achadas, "Nome do mantenedor em arquivo versionado:\n" + "\n".join(
        achadas
    )


def test_claude_md_sem_skill_pessoal(versionados: list[str]) -> None:
    """O ``CLAUDE.md`` e a pasta ``.claude/`` não apontam para skills pessoais."""
    alvos = [c for c in versionados if c == "CLAUDE.md" or c.startswith(".claude/")]
    achadas = _violacoes(alvos, _SKILL_PESSOAL, frozenset())
    assert not achadas, "Skill pessoal citada para quem clonou:\n" + "\n".join(achadas)
