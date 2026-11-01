# Dependências e cache: detalhes

Mapa: vai mexer no `pyproject.toml`, no `uv.lock`, em `exclude-newer` ou no `CACHES` do `settings.py`? Leia antes.

## Manifesto e lock (uv)

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

## Quarentena de 7 dias (uv)

`[tool.uv] exclude-newer = "7 days"` faz o lock resolver só versões publicadas há 7 dias ou mais
(defesa de supply chain). `exclude-newer-package` abre exceções pontuais e temporárias, cada uma com
o motivo e a data de remoção no comentário do `pyproject.toml` (hoje: nenhuma).

## Cache do rate limit

`FileBasedCache` em `django_cache/`, e não `LocMemCache`: o cache `LocMemCache` é por processo e, com
mais de um worker do gunicorn, o limite por IP do formulário de contato seria multiplicado pelo número
de workers (achado da auditoria de segurança). A pasta é criada em runtime e fica no `.gitignore`.
