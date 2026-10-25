# Dependências e cache: detalhes

Mapa: vai mexer em `exclude-newer` do `pyproject.toml` ou no `CACHES` do `settings.py`? Leia antes.

## Quarentena de 7 dias (uv)

`[tool.uv] exclude-newer = "7 days"` faz o lock resolver só versões publicadas há 7 dias ou mais
(defesa de supply chain). `exclude-newer-package` abre exceções pontuais e temporárias, cada uma com
o motivo e a data de remoção no comentário do `pyproject.toml` (hoje: `certifi`, por causa de uma
advisory CRITICAL; remover depois de 2026-10-27).

## Cache do rate limit

`FileBasedCache` em `django_cache/`, e não `LocMemCache`: o cache `LocMemCache` é por processo e, com
mais de um worker do gunicorn, o limite por IP do formulário de contato seria multiplicado pelo número
de workers (achado da auditoria de segurança). A pasta é criada em runtime e fica no `.gitignore`.
