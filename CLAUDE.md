# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com o código neste repositório.

## Visão Geral do Projeto

Portfólio profissional pessoal de Ryan Morais, construído com Django 6.0.
Projeto educacional de app único (`app_portfolio`) que serve uma página única
(a home): perfil do desenvolvedor, projetos, habilidades técnicas,
estatísticas de destaque e um formulário de contato com camadas anti-spam.
Deploy alvo: PythonAnywhere (processo único, SQLite em dev, PostgreSQL
opcional em produção via `psycopg2-binary`).

## Comandos Comuns

```bash
# Sincronizar o ambiente (.venv) a partir do uv.lock — dev: runtime + grupo dev (padrão)
uv sync

# Ambiente de produção: runtime + extras de prod (gunicorn, psycopg2-binary), sem ferramentas de dev
uv sync --no-dev --extra prod

# Gerenciar dependências (atualiza pyproject.toml + uv.lock automaticamente)
uv add <pacote>                       # dependência de runtime
uv add --dev <pacote>                 # ferramenta de desenvolvimento
uv remove <pacote>
uv lock --upgrade-package <pacote>    # atualiza só um pacote no lock

# Iniciar servidor de desenvolvimento (requer .env com SECRET_KEY)
uv run python manage.py runserver

# Migrações do banco de dados
uv run python manage.py makemigrations
uv run python manage.py migrate

# Criar superusuário para o Admin
uv run python manage.py createsuperuser

# Coletar arquivos estáticos (pré-deploy)
uv run python manage.py collectstatic --noinput

# Executar todos os testes
uv run pytest

# Executar um teste específico
uv run pytest app_portfolio/tests.py::TestSegurancaContato::test_rate_limit_blocking -v

# Executar testes com relatório de cobertura
uv run pytest --cov=app_portfolio --cov-report=term-missing

# Linting, formatação e type checking (config centralizada em pyproject.toml)
uv run ruff check .                        # Lint (substitui flake8 + isort)
uv run ruff check --fix .                  # Corrige automaticamente o que for seguro
uv run black .                             # Formatação
uv run mypy app_portfolio portfolio        # Verificação de tipos estáticos (mypy + django-stubs)

# Auditoria de dependências (CVEs conhecidas)
uv run pip-audit

# Checagem de postura de produção (SSL, HSTS, cookies, headers)
DEBUG=False uv run python manage.py check --deploy
```

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto. `SECRET_KEY` é a única variável
obrigatória (o servidor não sobe sem ela — `settings.py` levanta `ValueError`
com o caminho verificado). O arquivo `.env.example` (commitado no repositório)
serve de template documentado com todos os placeholders.

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `SECRET_KEY` | **obrigatória** | Chave secreta do Django |
| `DEBUG` | `False` | Defina como `True` só em desenvolvimento local |
| `ADMIN_URL` | `admin/` | Caminho do painel Admin — troque em produção para dificultar brute-force automatizado |
| `ALLOWED_HOSTS` | `*` (dev) | Lista de hosts permitidos em produção, separados por vírgula; vazio em produção rejeita todo host (falha fechada) |
| `EMAIL_USER` | — | Conta Gmail que envia (e recebe) as notificações do formulário de contato |
| `EMAIL_PASS` | — | **Senha de app** do Gmail (não a senha normal da conta) |

## Arquitetura

### Estrutura do projeto

```
portfolio/           # Configuração do projeto Django (settings, urls raiz, wsgi/asgi)
app_portfolio/        # A única aplicação
  models.py           # Todos os modelos de dados
  views.py             # View única (home): GET da vitrine + POST do formulário de contato
  forms.py             # MensagemContatoForm (ModelForm)
  admin.py             # Admin customizado para cada modelo
  utils.py             # converter_para_webp() — conversor universal de imagem
  urls.py              # URLs da aplicação (só a home)
  tests.py             # Suíte de testes (pytest) — um arquivo só, ver "Qualidade" abaixo
  migrations/
templates/            # Templates HTML na raiz do projeto (não dentro de app_portfolio)
  base.html
  home.html            # Única página: Hero, Sobre, Projetos, Habilidades, Contato
static/
  css/styles.css
  js/main.js           # JavaScript vanilla (menu mobile, formulário AJAX, notificações, filtros)
  icons/                # SVGs de UI, tecnologias e redes sociais
pyproject.toml         # Gerenciado com uv. [project]=runtime, [dependency-groups].dev, [project.optional-dependencies].prod + config das ferramentas (ruff, black, mypy, pytest)
uv.lock                # Lock único gerado por `uv lock` — todo o grafo pinado (NUNCA editar à mão)
.venv/                 # Ambiente virtual gerenciado pelo uv (gitignored; criado por `uv sync`)
.env.example           # Template documentado de variáveis de ambiente (commitado no repo)
.github/                # Serviços do GitHub (commitado)
  workflows/ci.yml       # CI: job "qualidade" (ruff/black/mypy/pytest) + job "seguranca" (pip-audit + check --deploy); em push na main e em PR
  dependabot.yml         # PRs semanais de atualização de dependências (uv + github-actions)
specs/                  # Especificações (spec-driven development); ver specs/README.md
  README.md              # Metodologia, convenções e índice das specs
  NNN-feature/            # requirements.md + design.md + tasks.md por feature
docs/
  stack.md                # Mapa de cada tecnologia da stack: o que faz, por que foi escolhida, o que estudar
```

### Modelos (em `models.py`)

1. **Auxiliares** — `Tecnologia` (badge + ícone, `mostrar_no_home` filtra a
   seção de ícones), `CategoriaProjeto` (agrupamento por `slug`,
   `CategoriaHabilidade`.
2. **Identidade** — `Perfil` (sem constraint de singleton — convenção de uso,
   não regra de negócio; um segundo registro faria `Perfil.objects.first()`
   retornar algo arbitrário).
3. **Portfólio** — `Projeto` (ordenado por `ordem`, M2M com `Tecnologia`,
   `categoria_projeto` opcional via `SET_NULL`, `link_github` opcional).
4. **Habilidades** — `Habilidade` (FK `CategoriaHabilidade`, `progresso` 0-100
   sem validação de range — confiança no preenchimento via Admin).
5. **Estatísticas** — `Estatistica` (números de destaque na Hero;
   `destaque_sobre` também exibe na seção Sobre).
6. **Contato** — `MensagemContato` (`mensagem` com `MaxLengthValidator(5000)`
   — adicionado na auditoria de segurança desta modernização).

Ver `specs/001-vitrine-portfolio/` e `specs/002-formulario-contato/` para o
detalhamento completo de requisitos e decisões de design de cada área.

### Tratamento de imagens

`utils.converter_para_webp()` é chamado no `save()` de `Perfil` (campo `foto`)
e `Projeto` (campo `imagem`).

- **Qualidade**: comprime para WebP com `quality=80`.
- **Skip automático**: se a imagem já estiver em WebP, retorna `(None, None)`.
- **Transparência**: RGBA/P convertidos para RGBA (preserva alpha); demais
  modos vão para RGB.
- **`save=False`**: usado em `image_field.save(novo_nome, conteudo,
  save=False)` para evitar recursão infinita (não chama o `save()` do model
  de novo).

Ao adicionar um novo model com `ImageField`, siga o mesmo padrão: sobrescreva
`save()`, chame `converter_para_webp()`, cheque `if novo_conteudo and
novo_nome:` (os dois juntos — `mypy` não infere que são não-`None` juntos a
partir de checar só um) e use `save=False`.

### Formulário de contato (em `views.py`)

Tudo roda dentro da view `home`, no ramo `if request.method == "POST"`, em
sequência:

1. **Honeypot** — campo oculto `honeypot`; preenchido → redirect silencioso,
   nada é salvo.
2. **Rate limit** — cache (`LocMemCache`) por `contact_limit_{REMOTE_ADDR}`,
   janela de 600s, ativado **só depois** do envio de e-mail suceder.
3. **Validação** — `MensagemContatoForm` (ModelForm).
4. **Sanitização** — `bleach.clean(mensagem, tags=[], strip=True)` antes de
   salvar (só o campo `mensagem`; `nome`/`assunto` não passam por `bleach`).
5. **Envio de e-mail** — `send_mail()` síncrono; falha é capturada e logada
   (`logger.exception`), nunca propaga — a mensagem já salva no banco não é
   perdida.
6. **Resposta híbrida** — header `X-Requested-With: XMLHttpRequest` decide
   entre `JsonResponse` (AJAX) e `redirect`/`messages` (HTML tradicional).

Ver `specs/002-formulario-contato/` para os critérios de aceite completos e
os ADRs (por que honeypot+rate limit em vez de CAPTCHA, por que o rate limit
ativa só após o envio, etc.).

> ⚠️ **Não regredir:** os testes desta feature (`app_portfolio/tests.py`)
> dependem da fixture autouse `disable_real_email`, que troca
> `EMAIL_BACKEND` para `locmem` durante a suíte. Sem ela, `send_mail()`
> tentaria conectar ao SMTP real do Gmail configurado em `settings.py` a cada
> teste — lento, dependente de rede, e capaz de enviar e-mail de verdade se o
> `.env` local tiver credenciais reais.

### Configurações notáveis (em `portfolio/settings.py`)

Um único `settings.py` para dev e produção, ramificado por `if not DEBUG:` —
sem `settings/base.py` + `dev.py` + `prod.py` (decisão de escala, ver
`specs/003-configuracao-seguranca/design.md`, ADR-01).

**Middleware (ordem importa):**
```
SecurityMiddleware → WhiteNoiseMiddleware → SessionMiddleware → CommonMiddleware →
CsrfViewMiddleware → AuthenticationMiddleware → MessageMiddleware →
XFrameOptionsMiddleware → CSPMiddleware
```

**Segurança em produção** (`DEBUG=False` ativa automaticamente):
- `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE = True`
- HSTS: 1 ano, incluindo subdomínios e preload
- CSP via `django-csp`: `script-src 'self'` (sem `'unsafe-inline'` — corrigido
  na auditoria desta modernização, nenhum template usa script inline);
  `style-src` mantém `'unsafe-inline'` (2 atributos `style=""` inline na
  barra de progresso de habilidades)
- URL do Admin ofuscada via `ADMIN_URL` (defesa em profundidade, não
  substitui autenticação forte)

> ⚠️ **Não regredir:** ao adicionar qualquer `<script>` inline num template,
> revise `CSP_SCRIPT_SRC` antes — o navegador bloqueia silenciosamente (só no
> console, sem erro no servidor). Ver `specs/003-configuracao-seguranca/`.

**Arquivos estáticos:** WhiteNoise com `CompressedStaticFilesStorage`.
`collectstatic` é obrigatório antes do deploy.

**Banco de dados:** SQLite em desenvolvimento; PostgreSQL em produção via
`psycopg2-binary` (extra `prod`), configurado manualmente em `DATABASES` (sem
`dj-database-url` — troca direta na config quando o deploy usa Postgres).

**E-mail:** SMTP do Gmail fixo (`smtp.gmail.com:587`); `EMAIL_SSL_CONTEXT`
via `certifi` para funcionar em qualquer SO. Requer "Senha de App" do Google,
não a senha normal da conta.

## Convenções

- **Idioma do código**: português — projeto pessoal/educacional (ver
  `/idioma` nas instruções globais).
- **Estilo de construção de arquivos** (docstrings, type hints, comentários,
  réguas de seção): ver a skill `/estilo-arquivos` — não repetido aqui.

## Qualidade e Automação (`pyproject.toml`)

Toda a configuração das ferramentas de qualidade é centralizada no
`pyproject.toml` (PEP 518): `black`, `ruff` (lint + isort), `pytest`,
`coverage` e `mypy` (modo strict, com `django-stubs`). A suíte de testes
relaxa `disallow_untyped_defs`/`disallow_incomplete_defs` porque usa fixtures
do `pytest-django` (`client`, `settings`) injetadas por parâmetro, sem tipo
prático a anotar sem importar internals do pytest.

**Fluxo de qualidade (rodar a partir da raiz, antes de commitar):**
```bash
uv run ruff check --fix .                  # 1. lint + ordena imports (ALTERA arquivos)
uv run black .                             # 2. formata (ALTERA arquivos)
uv run mypy app_portfolio portfolio        # 3. checa tipos (NÃO altera, só reporta)
uv run pytest                              # 4. roda os testes
```

`app_portfolio/tests.py` é um arquivo único (não uma pasta `tests/`) — o
projeto tem uma única view e um punhado de models, não há volume que
justifique a divisão em múltiplos arquivos por módulo testado (diferente do
`hub-ryan-morais`, que tem um app bem maior).

**CI no GitHub Actions** (`.github/workflows/ci.yml`): roda em todo push na
`main` e em todo `pull_request`, com dois jobs independentes: **`qualidade`**
(`ruff check` → `black --check` → `mypy app_portfolio portfolio` → `pytest`)
e **`seguranca`** (`pip-audit` + `manage.py check --deploy`, `DEBUG=False`).
Sem CodeQL — em repo privado exige GitHub Advanced Security (pago); o
Dependabot (`.github/dependabot.yml`, ecossistemas `uv` + `github-actions`)
cobre a varredura contínua de dependências.

## Spec-Driven Development (em `specs/`)

A pasta `specs/` documenta cada feature em três arquivos versionados —
`requirements.md` (o quê/porquê + critérios de aceite em **Given/When/Then**),
`design.md` (arquitetura + ADRs) e `tasks.md` (quebra rastreável `tarefa →
requisito`). As três specs atuais foram reconstruídas por **engenharia
reversa** do código (`status: concluído`), numa auditoria de segurança +
modernização de infraestrutura conduzida em 2026-09. A metodologia e o
índice completo estão em `specs/README.md`.

## Gestão de Dependências (uv)

O projeto é gerenciado pelo **uv** (substitui o antigo `pip` +
`requirements/*.txt`). A "parte humana" fica num só lugar — o
`pyproject.toml`:

- **`[project] dependencies`** — dependências **diretas** de runtime
  (Django, Pillow, whitenoise, bleach, django-csp, python-dotenv, certifi).
- **`[dependency-groups] dev`** — ferramentas de desenvolvimento (ruff,
  black, mypy, django-stubs, pytest, pip-audit…). `uv sync` instala por
  padrão; `uv sync --no-dev` exclui.
- **`[project.optional-dependencies] prod`** — extras de produção
  (`gunicorn`, `psycopg2-binary`). Instale com `uv sync --extra prod`.
- **`[tool.uv] package = false`** — é uma aplicação Django, não uma lib a ser
  empacotada.

Liste apenas **diretas** no `pyproject.toml`; as transitivas (`asgiref`,
`sqlparse`, `tzdata`, `webencodings`) são resolvidas automaticamente e não
aparecem lá.

**`uv.lock`** trava o grafo **completo** em versões exatas. Gerado/atualizado
por `uv lock` (ou automaticamente por `uv add`/`uv remove`) e **nunca editado
à mão**. Commite sempre o `pyproject.toml` **e** o `uv.lock`.
