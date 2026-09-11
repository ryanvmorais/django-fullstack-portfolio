---
feature: Formulário de contato (anti-spam, sanitização e notificação por e-mail)
status: concluído
data: 11/09/2026
relacionado:
  - 001-vitrine-portfolio
  - 003-configuracao-seguranca
origem: engenharia reversa do código existente (app_portfolio)
---

# Tasks — Formulário de Contato

## Etapa 0 — Estado original (antes desta sessão de modernização)

- [x] `MensagemContatoForm` (ModelForm) + `MensagemContato` (model) implementados. — RF-04
- [x] Honeypot no template (`display:none`, `tabindex="-1"`) + verificação na view. — RF-01
- [x] Rate limit por IP via `LocMemCache`, janela de 600s. — RF-02
- [x] Sanitização com `bleach.clean(tags=[], strip=True)` no campo `mensagem`. — RF-03
- [x] `send_mail()` síncrono com captura de exceção. — RF-05
- [x] Respostas híbridas HTML/AJAX via header `X-Requested-With`. — RF-06
- [x] `MensagemContatoAdmin` com todos os campos de conteúdo `readonly`. — RF-07
- [x] Testes originais (`test_contato_xss_sanitization`, `test_rate_limit_blocking`,
      `test_contato_honeypot_bot_protection`).

## Etapa 1 — Correções da auditoria de segurança (esta sessão)

- [x] `app_portfolio/models.py`: `mensagem` ganhou `MaxLengthValidator(5000)`
      + migração `0022_alter_mensagemcontato_mensagem`. — RF-04 (achado BAIXA:
      TextField sem limite permitia payload arbitrariamente grande)
- [x] `app_portfolio/views.py`: `except Exception: print(...)` trocado por
      `logger.exception(...)` (achado BAIXA: erro de SMTP não aparecia em log
      estruturado). — RF-05
- [x] `portfolio/settings.py`: `CSP_SCRIPT_SRC` removeu `'unsafe-inline'`
      (nenhum script inline usado pelo formulário ou pelo resto do site). — RNF-03
- [x] `static/js/main.js`: `showNotification()` passou a usar `textContent`
      em vez de interpolar `message` no `innerHTML` (achado BAIXA: sink de
      DOM XSS latente, hoje não explorável pois `data.message` só recebe
      strings fixas do backend).
- [x] Portão de qualidade após cada correção. — `pytest` verde (6 testes
      originais + fixes, antes de expandir a suíte na Etapa 2)

## Etapa 2 — Modernização e expansão de testes (esta sessão)

- [x] `pytest.ini` corrigido (docstring inválida impedia qualquer teste de
      rodar — bloqueava inclusive a verificação das correções da Etapa 1).
- [x] Fixture `disable_real_email` adicionada: sem ela, os testes desta
      feature disparavam `send_mail()` contra o SMTP real do Gmail
      configurado em produção. — RNF-01
- [x] `test_contato_envia_email_com_sucesso` — valida `mail.outbox`. — RF-05
- [x] `test_contato_ajax_sucesso_retorna_json` — valida contrato JSON de
      sucesso. — RF-06
- [x] `test_contato_ajax_bloqueio_retorna_429` — valida contrato JSON de
      rate limit. — RF-02, RF-06
- [x] `test_contato_erro_envio_email` — mocka `send_mail` para validar o
      caminho de falha (HTTP 500 + JSON de erro). — RF-05, RF-06
- [x] `test_contato_ajax_dados_invalidos_retorna_400` — valida contrato JSON
      de formulário inválido. — RF-06
- [x] Type hints completos em `views.py` (`home(request: HttpRequest) ->
      HttpResponse`) e `forms.py`/`models.py` correspondentes.
- [x] Portão de qualidade. — `ruff check`, `black --check`,
      `mypy app_portfolio portfolio` e `pytest` verdes (13 testes no total do
      app, cobertura de `views.py` em 100%).

## Etapa 3 — Documentação (esta sessão)

- [x] Esta spec (`002-formulario-contato/`) escrita por engenharia reversa,
      incluindo as correções da Etapa 1 como parte do histórico. — origem
