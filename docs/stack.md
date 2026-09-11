# A stack, e os porquês

Cada tecnologia que sustenta este projeto, o que ela faz, por que foi
escolhida em vez da alternativa, e os conceitos que valem a pena estudar
primeiro se ela for nova para você.

Este documento não é exaustivo — o grafo completo de versões fica travado no
`uv.lock`, e as decisões específicas de cada feature vivem nos blocos
`### ADR-N` de `specs/*/design.md`. Esta página é o mapa: a forma do projeto e
o raciocínio por trás de cada peça.

O projeto é um único app Django servindo uma página (a home), com o banco de
dados alimentado pelo Django Admin:

```
Django Admin (escrita)  ──►  SQLite (db.sqlite3)  ──►  view home()  ──►  home.html
                                                              │
                                                    formulário de contato
                                                              │
                                                        SMTP (Gmail)
```

---

## Linguagem e packaging

### Python 3.14

O runtime de todo o backend. 3.14 é a versão estável mais atual da linguagem
no momento desta modernização (setembro/2026).

**Por que esta:** política do projeto é sempre a versão estável mais recente,
não a mais antiga "que ainda funciona" — evita acumular dívida de atualização.

**Estudar:** sintaxe moderna de type hints (`X | None`, `list[str]`), f-strings,
o modelo de objetos do Django (models, querysets, managers).

### uv

Gerenciador de pacotes e ambientes virtuais Python (da Astral, criadora do
Ruff). Substitui `pip` + `venv` manual. `uv sync` instala o grafo travado do
`uv.lock`; `uv run` executa dentro do ambiente; `uv lock` resolve as versões.

**Por que esta, e não `pip` + `requirements.txt`:** o projeto usava `pip` com
três arquivos (`requirements/base.txt`, `local.txt`, `production.txt`)
mantidos à mão, sem lockfile real — duas pessoas rodando `pip install`
podiam acabar com grafos de dependência diferentes. O `uv.lock` trava
**tudo** (diretas e transitivas) em versões exatas, e `uv` é uma ordem de
magnitude mais rápido para instalar.

**Estudar:** `uv sync` / `uv sync --extra prod`, `uv run <comando>`, `uv add`
/ `uv lock`, a diferença entre `[project.dependencies]` (runtime),
`[project.optional-dependencies]` (extras, aqui só `prod`) e
`[dependency-groups]` (ferramentas de dev).

**Docs:** [docs.astral.sh/uv](https://docs.astral.sh/uv/)

---

## Framework e núcleo da aplicação

### Django 6.0

O framework web: ORM, sistema de templates, Admin automático, roteamento,
middlewares de segurança (CSRF, clickjacking, HSTS). É o núcleo em torno do
qual todo o resto do projeto gira.

**Por que este:** o Admin gerado automaticamente a partir dos models é o que
permite editar todo o conteúdo do portfólio (perfil, projetos, habilidades)
sem escrever nenhuma tela de CRUD — decisivo para um projeto solo. Frameworks
mais leves (Flask, FastAPI) exigiriam construir isso à mão.

**Estudar:** o ciclo `Model → View → Template`, `ModelForm` (usado no
formulário de contato), o sistema de `middleware` (ordem importa — ver
`portfolio/settings.py`), `select_related`/`prefetch_related` (otimização de
queries usada na view `home`).

**Docs:** [docs.djangoproject.com](https://docs.djangoproject.com/) ·
[Django Girls Tutorial](https://tutorial.djangogirls.org/) (introdução)

### Pillow

Biblioteca de processamento de imagem. Usada em `app_portfolio/utils.py`
(`converter_para_webp`) para converter toda imagem enviada via Admin
(foto de perfil, imagem de projeto) para o formato WebP antes de salvar.

**Por que esta:** é a biblioteca de imagem padrão de fato do ecossistema
Python — o próprio `ImageField` do Django já depende dela para validar
uploads.

**Estudar:** `Image.open`/`Image.save`, o parâmetro `quality` na exportação
WebP, a diferença entre os modos de cor `RGB`/`RGBA`/`P` (por que o código
converte para `RGBA` só quando há transparência).

**Docs:** [pillow.readthedocs.io](https://pillow.readthedocs.io/)

### whitenoise

Serve os arquivos estáticos (CSS, JS, ícones) diretamente pelo processo
Django, com compressão e cache-busting automáticos — sem precisar de um
Nginx ou CDN dedicado.

**Por que este:** o deploy é um único processo no PythonAnywhere; adicionar
um servidor de estáticos separado seria complexidade desnecessária nessa
escala.

**Estudar:** `CompressedStaticFilesStorage`, o comando `collectstatic`
(obrigatório antes do deploy), a posição do `WhiteNoiseMiddleware` logo após
o `SecurityMiddleware` em `MIDDLEWARE`.

**Docs:** [whitenoise.readthedocs.io](https://whitenoise.readthedocs.io/)

### bleach

Sanitizador de HTML. Usado em `app_portfolio/views.py` para remover qualquer
tag HTML do campo `mensagem` do formulário de contato antes de salvar no
banco — a principal defesa contra XSS armazenado do projeto.

**Por que este:** é uma biblioteca madura e específica para sanitização
(diferente de tentar escrever regex própria, que quase sempre tem brechas).

**Estudar:** `bleach.clean(texto, tags=[], strip=True)` (a chamada exata
usada aqui — lista vazia de tags permitidas remove todo HTML).

**Docs:** [bleach.readthedocs.io](https://bleach.readthedocs.io/)

### django-csp

Adiciona o header `Content-Security-Policy` a toda resposta, configurável via
`CSP_*` em `settings.py`. É a camada que limita de onde o navegador pode
carregar/executar script, estilo e imagem.

**Por que este:** é a integração padrão de CSP para Django; escrever o header
manualmente em um middleware próprio duplicaria uma solução já testada.

**Estudar:** as diretivas `default-src`/`script-src`/`style-src`, por que
`'unsafe-inline'` enfraquece a defesa contra XSS (corrigido em `script-src`
na auditoria de segurança desta sessão — ver `specs/003-configuracao-seguranca/`).

**Docs:** [django-csp.readthedocs.io](https://django-csp.readthedocs.io/)

### python-dotenv

Carrega variáveis de um arquivo `.env` (nunca versionado) para
`os.environ`, usado em `settings.py` para `SECRET_KEY`, `DEBUG`, credenciais
de e-mail, etc.

**Por que este:** é a forma padrão de manter segredos fora do código sem
depender de um serviço de secrets externo — proporcional a um projeto solo.

**Estudar:** `load_dotenv(dotenv_path=...)`, o padrão "12-factor app"
(configuração via ambiente, não hardcoded).

**Docs:** [github.com/theskumar/python-dotenv](https://github.com/theskumar/python-dotenv)

### certifi

Fornece o pacote de certificados raiz confiáveis (Mozilla CA bundle). Usado
em `settings.py` para montar o `EMAIL_SSL_CONTEXT` que permite ao Django
autenticar via TLS no SMTP do Gmail em qualquer plataforma.

**Por que este:** o Python nem sempre encontra o repositório de certificados
correto do sistema operacional (comum no Windows); `certifi` garante um
caminho confiável e portátil.

**Docs:** [github.com/certifi/python-certifi](https://github.com/certifi/python-certifi)

---

## Qualidade e automação (grupo dev)

### ruff

Linter e organizador de imports (substitui `flake8` + `isort` num binário
só, ordens de magnitude mais rápido — escrito em Rust). Primeiro passo do
portão de qualidade.

**Por que este, e não flake8/isort separados:** um binário só, configuração
centralizada no `pyproject.toml`, e reimplementa dezenas de plugins do
`flake8` nativamente.

**Estudar:** `uv run ruff check .` / `--fix`, os grupos de regra
(`E`/`W` pycodestyle, `F` pyflakes, `I` isort, `UP` pyupgrade) configurados
em `[tool.ruff.lint]`.

**Docs:** [docs.astral.sh/ruff](https://docs.astral.sh/ruff/)

### black

Formatador de código sem opções de configuração de estilo (aspas, quebra de
linha, espaçamento) — só o `line-length` é ajustável.

**Por que este:** elimina debate de estilo no time (ou consigo mesmo, revendo
o próprio código meses depois); é o formatador de fato do ecossistema Python.

**Docs:** [black.readthedocs.io](https://black.readthedocs.io/)

### mypy + django-stubs

Verificador de tipos estático. `django-stubs` ensina ao `mypy` os tipos do
Django (querysets, campos de model, `HttpRequest`) que a biblioteca em si não
anota.

**Por que este:** sem `django-stubs`, o `mypy` não entende o ORM do Django
(ex.: que `Model.objects.filter()` devolve um `QuerySet[Model]`) e gera ruído
demais para ser útil num projeto Django.

**Estudar:** `uv run mypy app_portfolio portfolio`, a diferença entre
`disallow_untyped_defs` e `disallow_incomplete_defs` (por que a suíte de
testes relaxa os dois — fixtures do `pytest-django` injetadas por parâmetro
não têm tipo prático de anotar).

**Docs:** [mypy.readthedocs.io](https://mypy.readthedocs.io/) ·
[github.com/typeddjango/django-stubs](https://github.com/typeddjango/django-stubs)

### pytest + pytest-django + pytest-cov

Framework de testes. `pytest-django` integra o `pytest` ao ciclo de vida do
Django (banco de teste, fixtures `client`/`settings`/`django_db`);
`pytest-cov` mede cobertura.

**Por que este, e não `unittest`/`TestCase` puro do Django:** fixtures
(`@pytest.fixture`) compõem melhor que herança de classe para os cenários
deste projeto (troca de `EMAIL_BACKEND`, `MEDIA_ROOT` temporário,
`SECURE_SSL_REDIRECT` desligado — todos via fixtures autouse em `tests.py`).

**Estudar:** `@pytest.fixture(autouse=True)`, `@pytest.mark.django_db`,
`django_assert_max_num_queries` (usado para travar o teto de queries da
home).

**Docs:** [pytest-django.readthedocs.io](https://pytest-django.readthedocs.io/)

### pip-audit

Varre o grafo de dependências resolvido em busca de CVEs conhecidas
(banco de dados PyPA). Roda tanto manualmente (auditoria de segurança) quanto
no job `seguranca` do CI.

**Por que este:** é a ferramenta oficial do Python Packaging Authority para
esse fim — sem depender de um serviço SaaS de terceiros.

**Docs:** [pypi.org/project/pip-audit](https://pypi.org/project/pip-audit/)

### ipython

Console Python interativo mais rico que o `python` padrão (autocomplete,
highlight de sintaxe, histórico persistente). Conveniência de
desenvolvimento via `uv run python manage.py shell` (o Django detecta e usa
o IPython se disponível).

**Docs:** [ipython.readthedocs.io](https://ipython.readthedocs.io/)

---

## Peças menores

| Peça | Papel |
|---|---|
| `gunicorn` (extra `prod`) | Servidor WSGI de produção — só instalado com `uv sync --extra prod` |
| `psycopg2-binary` (extra `prod`) | Driver PostgreSQL para produção (dev usa SQLite) |
| `asgiref`, `sqlparse`, `tzdata` | Dependências transitivas do próprio Django, não importadas diretamente |
| `webencodings` | Dependência transitiva do `bleach` |

---

## O que deliberadamente não está na stack

- **PostgreSQL em desenvolvimento** — SQLite é suficiente para um projeto de
  um único usuário/administrador; PostgreSQL só entra via `psycopg2-binary`
  no deploy de produção.
- **Redis / cache distribuído** — o rate limit do formulário de contato usa
  `LocMemCache` (em memória, por processo); o deploy atual é um único
  processo, então não há estado a sincronizar entre workers.
- **django-two-factor-auth / django-axes (2FA e brute-force no Admin)** —
  usados no `hub-ryan-morais` (projeto irmão, maior), mas decisão explícita
  de escala não trazer aqui: um único administrador, risco aceito (ver
  `specs/003-configuracao-seguranca/design.md`, ADR-04).
- **DRF (Django REST Framework) ou qualquer API** — o projeto não expõe
  endpoints JSON além das respostas AJAX do próprio formulário de contato
  (`JsonResponse` direto na view, sem serializer).
- **Celery / fila assíncrona** — o envio de e-mail é síncrono, dentro do
  ciclo de request; o volume de mensagens de contato de um portfólio pessoal
  não justifica a complexidade operacional de um worker separado.
- **Node.js / bundler de frontend** — `static/js/main.js` é JavaScript
  vanilla servido diretamente pelo `whitenoise`; não há build step de
  frontend.
