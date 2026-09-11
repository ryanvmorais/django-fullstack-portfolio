---
feature: Configuração e postura de segurança (settings, CSP, admin, deploy)
status: concluído
data: 11/09/2026
relacionado:
  - 002-formulario-contato
origem: engenharia reversa do código existente (portfolio/settings.py)
---

# Requisitos — Configuração e Segurança

> Reconstruído por engenharia reversa a partir de uma auditoria de segurança
> completa (5 camadas: dependências, SAST, segredos, configuração e revisão
> OWASP) conduzida nesta sessão. Cobertura: `manage.py check --deploy`
> (manual, não automatizado em teste) e verificação manual de cada
> configuração abaixo.

## 1. Contexto e problema

O projeto é deployado no PythonAnywhere a partir de um único `settings.py`
compartilhado entre dev e produção, diferenciado só por variáveis de
ambiente (`.env`, nunca commitado). Precisa ser seguro por padrão mesmo se
alguém esquecer de configurar algo em produção.

## 2. Objetivos

- Nunca subir com `SECRET_KEY` ausente ou com `DEBUG=True` por padrão.
- Aplicar hardening de produção (HTTPS, HSTS, cookies seguros) automaticamente
  quando `DEBUG=False`, sem exigir uma segunda config.
- Reduzir a superfície de XSS via Content Security Policy.
- Dificultar brute-force trivial no Admin via URL não previsível.
- Manter dependências sem CVEs conhecidos aplicáveis ao projeto.

## 3. Não-objetivos

- 2FA no Admin (existe no `hub-ryan-morais`, spec 012; não implementado aqui —
  ver "Perguntas em aberto").
- Rate limit distribuído (Redis) — `LocMemCache` é suficiente no deploy atual
  (ver spec 002, ADR-04).
- WAF/proteção de borda — fora do controle da aplicação Django.

## 4. Requisitos funcionais e critérios de aceite

### RF-01 — Falha rápida sem SECRET_KEY

- **Given** `.env` sem `SECRET_KEY` (ou variável vazia)
  **When** o Django tenta carregar `settings.py`
  **Then** uma `ValueError` explícita é levantada antes de qualquer outra
  configuração, citando o caminho do `.env` verificado.

### RF-02 — DEBUG seguro por padrão

- **Given** a variável `DEBUG` ausente do ambiente
  **When** `settings.py` é carregado
  **Then** `DEBUG` resolve para `False` (secure by default) — só vira `True`
  com o valor explícito `"true"` (case-insensitive) no `.env`.

### RF-03 — ALLOWED_HOSTS controlado por ambiente

- **Given** `DEBUG=True`
  **Then** `ALLOWED_HOSTS = ["*"]` (conveniência local).
- **Given** `DEBUG=False`
  **Then** `ALLOWED_HOSTS` vem exclusivamente do `.env` (`ALLOWED_HOSTS`,
  separado por vírgula); ausente, resolve para `[""]` — o Django rejeita
  todo host (falha fechada, não aberta).

### RF-04 — Hardening automático em produção

- **Given** `DEBUG=False`
  **Then** `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`,
  `CSRF_COOKIE_SECURE` ficam `True`, e HSTS é configurado para 1 ano
  (`SECURE_HSTS_SECONDS=31536000`) com `INCLUDE_SUBDOMAINS` e `PRELOAD`.
- **Given** `DEBUG=True`
  **Then** nenhuma dessas configurações é aplicada (evita quebrar o
  `runserver` local em HTTP).

### RF-05 — Content Security Policy

- **Given** qualquer resposta HTTP
  **Then** o header CSP é definido via `django-csp`: `default-src 'self'`,
  `script-src 'self'` (sem `'unsafe-inline'` — corrigido nesta sessão),
  `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`,
  `img-src 'self' data: https:`, `font-src 'self' https://fonts.gstatic.com`.

### RF-06 — URL do Admin ofuscada

- **Given** a variável `ADMIN_URL` no `.env`
  **Then** o painel administrativo é montado nesse caminho em vez do
  `admin/` padrão (`portfolio/urls.py`), dificultando brute-force automatizado
  contra o caminho previsível.

### RF-07 — Dependências sem CVE aplicável

- **Given** o grafo de dependências (`uv.lock`)
  **Then** `pip-audit` não reporta CVE cujo componente vulnerável seja
  efetivamente exercitado pelo projeto (ex.: Django 6.0.7 tinha
  `PYSEC-2026-3717`, um DoS em `django.contrib.gis` — não usado aqui;
  corrigido para 6.0.8 mesmo assim, por higiene de versão).

### RF-08 — Verificação de segurança automatizada em CI

- **Given** um push ou pull request na branch `main`
  **When** o workflow `.github/workflows/ci.yml` roda
  **Then** o job `seguranca` executa `pip-audit` (CVEs conhecidas) e
  `manage.py check --deploy` (postura de produção) — sinal visível no PR, sem
  bloquear o merge por si só.

## 5. Requisitos não-funcionais

- **RNF-01 (Segredos):** `.env`, `db.sqlite3` e `venv`/`.venv` nunca são
  versionados (`.gitignore`); confirmado sem achados em `detect-secrets` +
  `git ls-files` na auditoria desta sessão.
- **RNF-02 (SAST):** `semgrep scan --config auto` (459 regras, multi-linguagem)
  não encontrou padrão inseguro em `app_portfolio/` nem `portfolio/`.

## 6. Perguntas em aberto / decisões conhecidas

- Sem 2FA no Admin — risco aceito dado que é um projeto pessoal de baixo
  valor de alvo; reavaliar se o volume de acesso/edição crescer.
- Falha de envio de e-mail no fluxo HTML não é reportada ao usuário (ver spec
  002, RF-05) — não é uma falha de configuração, mas um gap de UX adjacente.
