---
feature: Vitrine do portfólio (perfil, projetos, habilidades, estatísticas)
status: concluído
data: 11/09/2026
relacionado:
  - 002-formulario-contato
origem: engenharia reversa do código existente (app_portfolio)
---

# Tasks — Vitrine do Portfólio

## Etapa 0 — Estado original (antes desta sessão de modernização)

- [x] Models `Perfil`, `Projeto`, `Tecnologia`, `CategoriaProjeto`,
      `CategoriaHabilidade`, `Habilidade`, `Estatistica` implementados,
      com 21 migrações incrementais. — RF-01, RF-02, RF-06, RF-07
- [x] View `home` com queries otimizadas (`select_related`/`prefetch_related`). — RF-02, RNF-01
- [x] `utils.converter_para_webp` + `save()` sobrescrito em `Perfil`/`Projeto`. — RF-05
- [x] `admin.py` com `list_editable` em `Tecnologia`, `Projeto`, `Estatistica`. — RF-08
- [x] Template `home.html` com todas as seções (Hero, Sobre, Projetos,
      Habilidades, Contato) e fallback de imagem estática. — RF-01 a RF-07
- [x] Testes originais (`test_home_status_code`, `test_perfil_creation`,
      `test_home_query_count`) cobrindo status HTTP, criação de model e teto
      de queries.

## Etapa 1 — Modernização (esta sessão)

- [x] `pytest.ini` corrigido (docstring inválida quebrava toda a suíte de
      testes — nenhum teste rodava antes desta correção). — pré-requisito
      para qualquer teste desta spec ser executável.
- [x] `TestConverterParaWebp` adicionado (`test_save_converte_imagem_para_webp`,
      `test_save_sem_imagem_nao_falha`), fechando a lacuna de cobertura do
      pipeline WebP. — RF-05
- [x] Fixture `media_root_tmp` adicionada para isolar uploads de teste do
      `media/` real do projeto.
- [x] Type hints completos em `models.py` (`__str__ -> str`,
      `save(*args: Any, **kwargs: Any) -> None`) e `utils.py`
      (`converter_para_webp`), e docstrings faltantes em `admin.py`
      (`CategoriaHabilidadeAdmin`, `EstatisticaAdmin`).
- [x] Migração `0022_alter_mensagemcontato_mensagem` (pertence à spec 002,
      não a esta — registrada aqui só porque roda no mesmo `migrate`).
- [x] Portão de qualidade. — `ruff check`, `black --check`,
      `mypy app_portfolio portfolio` e `pytest` verdes (13 testes, 97% de
      cobertura em `app_portfolio`).

## Etapa 2 — Documentação (esta sessão)

- [x] Esta spec (`001-vitrine-portfolio/`) escrita por engenharia reversa. — origem
- [x] `docs/stack.md` documenta `Pillow`/`whitenoise` (pipeline de imagem e
      estáticos usados por esta feature).
