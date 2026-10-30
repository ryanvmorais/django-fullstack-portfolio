# CI e automação: detalhes

Mapa: vai mexer em `.github/workflows/`, `.github/dependabot.yml` ou `.github/lighthouse/`? Leia antes.

## CI no GitHub Actions

`.github/workflows/ci.yml` roda em todo push na `main` e em todo `pull_request`, com dois jobs
independentes: **`qualidade`** (`ruff check` → `black --check` → `mypy app_portfolio portfolio` →
`pytest`) e **`seguranca`** (`pip-audit` + `manage.py check --deploy`, `DEBUG=False`).

O CodeQL (code scanning, grátis em repo público) roda no workflow próprio `codeql.yml`, em PR, na
`main` e uma vez por semana; não é check obrigatório. O Dependabot (`.github/dependabot.yml`, `uv` +
`github-actions`) cobre a varredura contínua de dependências.

## pip-audit semanal

O `pip-audit` roda toda segunda, às 09:00 de São Paulo (e à mão), sobre o `uv.lock`
(`.github/workflows/pip-audit.yml`), porque o CI só roda em push/PR e o Dependabot nem sempre abre PR. Run vermelho =
CVE no lock; a resposta é a `/atualizar-dependencias`.

## Lighthouse CI

`.github/workflows/lighthouse.yml` audita a Home em mobile e desktop, em PR que mude a página, no
push da `main` e à mão; **não é check obrigatório**. Sobe com `manage.py semear_dados_demo` (só
`DEBUG=True`). Limites em `.github/lighthouse/*.json`; `@lhci/cli` fixado em `LHCI_VERSION`.
Detalhes em `docs/stack.md`; teste em `app_portfolio/test_semear_dados_demo.py`.
