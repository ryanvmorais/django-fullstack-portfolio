---
feature: Vitrine do portfólio (perfil, projetos, habilidades, estatísticas)
status: concluído
data: 11/09/2026
relacionado:
  - 002-formulario-contato
origem: engenharia reversa do código existente (app_portfolio)
---

# Design — Vitrine do Portfólio

## 1. Visão geral

Tudo é renderizado por uma única view (`home`) e um único template
(`templates/home.html`, estendendo `base.html`). Não há roteamento por
recurso — o "banco de dados vira HTML" via contexto do Django, e o Admin é a
única interface de escrita.

## 2. Componentes

| Componente | Arquivo | Responsabilidade |
|---|---|---|
| `home` | `app_portfolio/views.py` | Monta `perfil`, `projetos`, `tech_icons`, `estatisticas`, `categorias_projetos`, `categorias_habilidades` |
| `Perfil` | `app_portfolio/models.py` | Dados do desenvolvedor; `save()` converte `foto` para WebP |
| `Projeto` | `app_portfolio/models.py` | Dados do projeto + `ordem`; `save()` converte `imagem` para WebP |
| `Tecnologia` | `app_portfolio/models.py` | Badge de tecnologia (M2M com `Projeto`); `mostrar_no_home` filtra os ícones da seção Habilidades |
| `CategoriaProjeto` | `app_portfolio/models.py` | Agrupamento por `slug`, usado no filtro client-side |
| `CategoriaHabilidade` / `Habilidade` | `app_portfolio/models.py` | Agrupamento de habilidades (FK) |
| `Estatistica` | `app_portfolio/models.py` | Números de destaque (Hero + Sobre) |
| `converter_para_webp` | `app_portfolio/utils.py` | Conversão universal de imagem para WebP, reusada por `Perfil` e `Projeto` |
| `*Admin` | `app_portfolio/admin.py` | Um `ModelAdmin` por modelo; `list_editable` para reordenação |

## 3. Modelo de dados

`Perfil`: `nome`, `cargo`, `foto` (WebP, opcional), `bio`, `bio_curta`,
`anos_experiencia`, `mostrar_progresso` (bool), `email_contato`, `telefone`,
`localizacao`, `status_trabalho`, `formacao`, `curriculo` (FileField),
`link_linkedin`, `link_github`. Sem constraint de singleton.

`Projeto`: `categoria_projeto` (FK `CategoriaProjeto`, `SET_NULL`, opcional),
`titulo`, `descricao` (≤170 caracteres sugerido via `help_text`), `imagem`
(WebP, opcional), `tecnologias` (M2M), `link_github` (opcional), `ordem` (int,
default 0). `Meta.ordering = ["ordem"]`.

`Tecnologia`: `nome`, `icone` (nome de arquivo SVG, ex.: `python.svg`),
`mostrar_no_home` (bool), `ordem`. `Meta.ordering = ["ordem", "nome"]`.

`CategoriaProjeto`: `nome`, `slug` (único, usado como `data-filter`).

`CategoriaHabilidade`: `nome`, `icone`. `Habilidade`: `categoria` (FK,
`CASCADE`), `nome`, `progresso` (int 0-100, sem `MinValueValidator`/
`MaxValueValidator` — confiança no preenchimento via Admin).

`Estatistica`: `titulo` (ex.: "5+"), `legenda`, `ordem`, `destaque_sobre`
(bool). `Meta.ordering = ["ordem"]`.

## 4. Interfaces

Sem rota própria além de `home` (`portfolio/urls.py` → `app_portfolio.urls`).
Contexto da `home`:

- `perfil` — `Perfil.objects.first()`
- `projetos` — `Projeto.objects.select_related("categoria_projeto").prefetch_related("tecnologias").all()`
- `tech_icons` — `Tecnologia.objects.filter(mostrar_no_home=True).order_by("ordem", "nome")`
- `estatisticas` — `Estatistica.objects.all()`
- `categorias_projetos` — `CategoriaProjeto.objects.all()` (sem filtro por ter projeto — ver RF-03)
- `categorias_habilidades` — `CategoriaHabilidade.objects.prefetch_related("habilidades").all()`

## 5. Decisões técnicas (ADRs)

### ADR-01 — Ordenação manual por `ordem`

- **Decisão:** `IntegerField`/`PositiveIntegerField ordem` + `Meta.ordering` +
  `list_editable` no Admin, em `Projeto`, `Tecnologia` e `Estatistica`.
- **Alternativas:** ordenação automática por data de criação/relevância.
- **Porquê:** o dono cura a vitrine manualmente; não há sinal de relevância
  algorítmica disponível (nº de estrelas no GitHub, tráfego, etc.).
- **Trade-off:** exige manutenção manual do campo `ordem` a cada novo registro.

### ADR-02 — Conversão de imagem para WebP no `save()` do model

- **Decisão:** `Perfil.save()` e `Projeto.save()` chamam
  `utils.converter_para_webp()` antes de `super().save()`, com `save=False`
  na chamada de `self.imagem.save(...)` para evitar recursão infinita.
- **Alternativas:** converter no upload via JavaScript (client-side); converter
  em um signal `pre_save` separado do model.
- **Porquê:** manter a lógica de imagem perto do model que a usa é mais direto
  neste projeto de apenas dois models com `ImageField`; um signal
  desacoplado ganharia sentido se o número de models crescesse (ver o mesmo
  padrão em escala maior no `hub-ryan-morais`, que usa signal reusável entre
  6 models).
- **Trade-off:** duplicação do bloco `if novo_conteudo and novo_nome:` entre
  os dois `save()` — aceitável no tamanho atual do projeto.

### ADR-03 — Portfólio sem detalhe nem rota própria

- **Decisão:** tudo (perfil, projetos, habilidades, estatísticas) é resolvido
  na única view `home`.
- **Porquê:** vitrine curta e estática o suficiente para não justificar
  `ListView`/`DetailView` dedicadas.

## 6. Impacto e dependências

- `imagem`/`foto` participam do pipeline WebP (`utils.py`); qualquer novo
  model com `ImageField` deve seguir o mesmo padrão (`save=False` na
  atribuição, chamada a `converter_para_webp` antes de `super().save()`).
- `CategoriaProjeto.slug` é consumido apenas no client-side
  (`static/js/main.js`, `data-filter`); mudanças de slug não quebram o
  backend, só o filtro visual.

## 7. Estratégia de testes

`TestPortfolioCore` (status 200 da home, criação de `Perfil`, teto de 10
queries) e `TestConverterParaWebp` (upload de PNG vira `.webp`; ausência de
imagem não falha o `save()`). Não há teste de snapshot do HTML renderizado —
a cobertura é sobre dados de contexto e queries, não sobre o markup.
