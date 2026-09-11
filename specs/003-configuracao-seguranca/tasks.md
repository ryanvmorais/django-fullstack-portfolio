---
feature: Configuração e postura de segurança (settings, CSP, admin, deploy)
status: concluído
data: 11/09/2026
relacionado:
  - 002-formulario-contato
origem: engenharia reversa do código existente (portfolio/settings.py)
---

# Tasks — Configuração e Segurança

## Etapa 0 — Estado original (antes desta sessão de modernização)

- [x] Validação de `SECRET_KEY` obrigatória (`ValueError` no import). — RF-01
- [x] `DEBUG` seguro por padrão (`False` se ausente). — RF-02
- [x] `ALLOWED_HOSTS` diferenciado por `DEBUG`. — RF-03
- [x] Hardening condicional (`SECURE_SSL_REDIRECT`, HSTS, cookies) só com
      `DEBUG=False`. — RF-04
- [x] CSP via `django-csp` (com `'unsafe-inline'` em `script-src`, corrigido
      na Etapa 1). — RF-05
- [x] URL do Admin ofuscada via `.env`. — RF-06

## Etapa 1 — Auditoria de segurança e correções (esta sessão)

- [x] Varredura completa em 5 camadas: dependências (`pip-audit`), SAST
      (`semgrep`, 459 regras/85 arquivos, 0 achados), segredos
      (`detect-secrets` + `git ls-files`, 0 achados versionados), configuração
      (`manage.py check --deploy` manual) e revisão OWASP manual.
- [x] `pip-audit` encontrou `PYSEC-2026-3717` em Django 6.0.7 (DoS em
      `django.contrib.gis`, não usado neste projeto). Django atualizado para
      6.0.8 em `pyproject.toml` mesmo assim, por higiene de versão. — RF-07
- [x] `CSP_SCRIPT_SRC` removeu `'unsafe-inline'` (nenhum script inline nos
      templates). — RF-05
- [x] Portão de qualidade após as correções. — `pytest` verde (6 testes
      originais, antes da expansão da suíte na spec 002)

## Etapa 2 — Modernização de infraestrutura (esta sessão)

- [x] Migração de `pip` + `requirements/*.txt` para `uv` (`pyproject.toml` +
      `uv.lock`). Não é um requisito funcional desta spec, mas sustenta o
      `pip-audit` reproduzível (`uv run pip-audit`) e o `mypy`/`ruff`/`black`.
- [x] `.github/dependabot.yml` criado (ecossistemas `pip` + `github-actions`,
      `weekly`/`monday`, `open-pull-requests-limit: 5`) — cobre a varredura
      contínua de dependências que o `pip-audit` manual não substitui.
- [x] `.github/workflows/ci.yml` criado com job `seguranca`
      (`pip-audit` + `manage.py check --deploy`), espelhando o padrão do
      `hub-ryan-morais` — fecha a lacuna registrada como "pergunta em aberto"
      na versão inicial desta spec (CI não automatizava a checagem de
      deploy).
- [x] Portão de qualidade completo. — `uv run ruff check .`,
      `uv run black --check .`, `uv run mypy app_portfolio portfolio`,
      `uv run pytest` verdes.

## Etapa 3 — Documentação (esta sessão)

- [x] Esta spec (`003-configuracao-seguranca/`) escrita por engenharia
      reversa, documentando tanto o estado original quanto as correções da
      auditoria. — origem
- [x] `docs/stack.md` documenta `django-csp`, `whitenoise`,
      `python-dotenv`, `certifi` e as ferramentas de qualidade
      (`ruff`/`black`/`mypy`/`pytest`/`pip-audit`).
