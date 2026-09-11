---
feature: Vitrine do portfólio (perfil, projetos, habilidades, estatísticas)
status: concluído
data: 11/09/2026
relacionado:
  - 002-formulario-contato
origem: engenharia reversa do código existente (app_portfolio)
---

# Requisitos — Vitrine do Portfólio

> Reconstruído por engenharia reversa. Cobertura em `app_portfolio/tests.py`
> (`TestPortfolioCore`, `TestConverterParaWebp`).

## 1. Contexto e problema

O site é uma página única (`home.html`) que funciona como currículo/portfólio
público: dados do desenvolvedor, projetos, habilidades técnicas e estatísticas
de destaque, todos editáveis via Django Admin sem precisar mexer em código.

## 2. Objetivos

- Exibir o perfil do desenvolvedor (bio, foto, contatos, currículo) sem
  hardcode no template.
- Exibir projetos com categoria, tecnologias associadas e link opcional ao
  GitHub, em ordem controlada manualmente.
- Exibir habilidades agrupadas por categoria, com toggle opcional de barra de
  progresso.
- Exibir estatísticas de destaque (ex.: "5+ anos de experiência") na Hero e na
  seção Sobre.
- Manter a home rápida (poucas queries) mesmo com o crescimento do conteúdo.

## 3. Não-objetivos

- Página de detalhe por projeto — a vitrine é a própria home.
- Busca ou paginação de projetos.
- Múltiplos perfis (o sistema assume um único registro de `Perfil`, mas não
  impõe isso via `unique` nem via `clean()` — é uma convenção de uso, não uma
  regra de negócio).

## 4. Personas

- **Visitante/recrutador** — navega a home para avaliar o desenvolvedor.
- **Administrador (o próprio Ryan)** — cadastra/edita perfil, projetos,
  habilidades e estatísticas pelo Django Admin.

## 5. Requisitos funcionais e critérios de aceite

### RF-01 — Exibição do perfil na home

- **Given** um registro de `Perfil` cadastrado
  **When** a home é renderizada
  **Then** exibe nome, cargo, bio (com quebras de linha via `linebreaks`),
  localização, status de trabalho, formação e link de currículo.
- **Given** nenhum `Perfil` cadastrado
  **Then** `Perfil.objects.first()` retorna `None` e o template usa os campos
  vazios sem lançar erro (variáveis de contexto Django toleram `None`).

### RF-02 — Projetos ordenados com categoria e tecnologias

- **Given** projetos com campo `ordem`
  **When** a home é renderizada
  **Then** exibe todos os projetos ordenados por `ordem` (menor primeiro), com
  `categoria_projeto` e `tecnologias` pré-carregadas (sem N+1).
- **Given** um projeto sem `categoria_projeto` (FK `SET_NULL`)
  **Then** o card é exibido sem quebrar (categoria ausente é tolerada no template).

### RF-03 — Filtro de categorias na UI

- **Given** categorias de projeto cadastradas
  **When** a home monta o contexto
  **Then** lista **todas** as categorias como botão de filtro, independente de
  terem projeto associado (o filtro real por `data-category` acontece no
  client-side, em `static/js/main.js`).

### RF-04 — Link GitHub opcional

- **Given** um projeto com `link_github` preenchido
  **Then** o card exibe o botão "Ver no GitHub".
- **Given** `link_github` vazio
  **Then** o botão aponta para `href=""` (o campo é opcional; o template não
  omite o link, apenas fica vazio).

### RF-05 — Ícone/imagem do projeto e do perfil em WebP

- **Given** uma `imagem` (Projeto) ou `foto` (Perfil) enviada via Admin
  **When** o registro é salvo
  **Then** a imagem é convertida para WebP antes de persistir (ver RF-01 da
  spec 003 não se aplica; regra própria em `utils.converter_para_webp`).
- **Given** nenhuma imagem enviada
  **Then** o template usa um ícone estático de fallback
  (`static/icons/default_projeto.webp` / `avatar_padrao.webp`).

### RF-06 — Habilidades agrupadas por categoria

- **Given** categorias de habilidade com habilidades associadas (FK)
  **When** a home é renderizada
  **Then** cada categoria lista suas habilidades; sem habilidades, exibe
  "Nenhuma habilidade cadastrada." (`{% empty %}`).
- **Given** `Perfil.mostrar_progresso = True`
  **Then** cada habilidade exibe o percentual numérico e a barra visual
  (`aria-valuenow`); com `False`, nenhum dos dois aparece.

### RF-07 — Estatísticas de destaque

- **Given** registros de `Estatistica` ordenados por `ordem`
  **When** a home é renderizada
  **Then** todos aparecem na Hero; os marcados com `destaque_sobre=True`
  também aparecem no badge da seção Sobre.

### RF-08 — Reordenação e edição em massa no Admin

- **Given** o Admin de `Tecnologia`, `Projeto` ou `Estatistica`
  **Then** os campos `ordem` (e, em `Tecnologia`, `mostrar_no_home`) são
  editáveis diretamente na listagem (`list_editable`), sem abrir o registro.

## 6. Requisitos não-funcionais

- **RNF-01 (Performance):** a home usa `select_related("categoria_projeto")` +
  `prefetch_related("tecnologias")` em `Projeto`, e `prefetch_related("habilidades")`
  em `CategoriaHabilidade`, para evitar N+1. Coberto por
  `test_home_query_count` (teto de 10 queries).
- **RNF-02 (Robustez de upload):** a conversão WebP é limitada pelo guard
  default do Pillow (`Image.MAX_IMAGE_PIXELS`); não há limite explícito de
  tamanho de arquivo no nível da aplicação — mitigado pelo fato de o upload
  só estar disponível a usuários `is_staff` no Admin.

## 7. Perguntas em aberto

- Não há paginação para portfólios com muitos projetos; assume-se um número
  pequeno o suficiente para caber numa grade sem scroll interno.
- `Perfil` não impõe singleton por código (diferente do Hub, spec
  007-conteudo-institucional) — cadastrar um segundo `Perfil` no Admin faz
  `Perfil.objects.first()` retornar um registro arbitrário.
