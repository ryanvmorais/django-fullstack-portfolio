---
feature: Formulário de contato (anti-spam, sanitização e notificação por e-mail)
status: concluído
data: 11/09/2026
relacionado:
  - 001-vitrine-portfolio
  - 003-configuracao-seguranca
origem: engenharia reversa do código existente (app_portfolio)
---

# Design — Formulário de Contato

## 1. Visão geral

Toda a lógica vive na mesma view `home` que renderiza a vitrine (`GET`) — o
`POST` do formulário de contato é tratado como um ramo condicional dentro
dela, não uma view separada. Quatro camadas são aplicadas em sequência antes
de persistir: honeypot → rate limit → validação de formulário → sanitização.

## 2. Componentes

| Componente | Arquivo | Responsabilidade |
|---|---|---|
| `home` (ramo POST) | `app_portfolio/views.py` | Honeypot, rate limit, validação, sanitização, envio de e-mail, resposta híbrida |
| `MensagemContatoForm` | `app_portfolio/forms.py` | `ModelForm` — validação de campo (tipo/obrigatoriedade) herdada do model |
| `MensagemContato` | `app_portfolio/models.py` | Persistência; `mensagem` com `MaxLengthValidator(5000)` |
| `MensagemContatoAdmin` | `app_portfolio/admin.py` | Consulta somente leitura das mensagens recebidas |
| `bleach.clean` | biblioteca `bleach` | Remove todas as tags HTML do campo `mensagem` |
| `django.core.cache` (`LocMemCache`) | `portfolio/settings.py` | Armazena a chave `contact_limit_{ip}` do rate limit |
| Template `contact__form` | `templates/home.html` | Honeypot oculto via `display:none`, `{% csrf_token %}` |
| `contactForm` handler | `static/js/main.js` | Submissão via `fetch` com `X-Requested-With` e `X-CSRFToken` |

## 3. Modelo de dados

`MensagemContato`: `nome` (CharField 100), `email` (EmailField), `assunto`
(CharField 200), `mensagem` (TextField + `MaxLengthValidator(5000)`),
`data_envio` (`auto_now_add`), `lida` (bool, default `False`, não usada por
nenhuma view pública — só consulta manual no Admin).

Migração `0022_alter_mensagemcontato_mensagem` (desta sessão) adiciona o
validador de tamanho sem alterar o tipo de coluna (TextField no SQLite não tem
limite nativo; o validador é aplicado em nível de Django, via `full_clean()`
do `ModelForm`).

## 4. Interfaces

Sem rota própria — o formulário faz POST para a própria URL da home
(`action=""` no `<form>`). Contrato de resposta:

| Cenário | HTML | AJAX (`X-Requested-With`) |
|---|---|---|
| Honeypot preenchido | `redirect("home")` | idem (sem diferenciar) |
| Rate limit ativo | `messages.error` + redirect | `429` + `{"status": "error"}` |
| Formulário inválido | Re-renderiza `home.html` com erros do form | `400` + `{"status": "error", "message": "Dados inválidos."}` |
| Envio OK | `redirect("home")` | `200` + `{"status": "success", "message": "Mensagem enviada!"}` |
| Falha no SMTP | Re-renderiza sem feedback específico (ver RF-05, pergunta aberta) | `500` + `{"status": "error", "message": "Erro ao enviar e-mail."}` |

## 5. Decisões técnicas (ADRs)

### ADR-01 — Duas camadas anti-spam sem CAPTCHA (honeypot + rate limit)

- **Decisão:** honeypot (campo oculto) detecta bots ingênuos; rate limit por
  IP (`cache`, janela de 10 min) limita o custo de abuso mesmo que o honeypot
  seja contornado.
- **Alternativas:** reCAPTCHA/hCaptcha (Google/Cloudflare); throttling por
  `django-ratelimit`.
- **Porquê:** projeto educacional/pessoal de baixo volume — CAPTCHA de
  terceiro adicionaria dependência externa e fricção de UX para um risco que
  duas camadas simples já mitigam o suficiente.
- **Trade-off:** um bot sofisticado que preenche o honeypot corretamente e
  varia de IP a cada request não é bloqueado. Aceito dado o perfil de risco
  (site de portfólio pessoal, não um formulário de alto valor).

### ADR-02 — Sanitização com `bleach` em vez de confiar só no autoescape do Django

- **Decisão:** `bleach.clean(mensagem, tags=[], strip=True)` remove todo HTML
  do campo antes de salvar — mesmo o Django já autoescapando por padrão nos
  templates.
- **Porquê:** defesa em profundidade — o valor sanitizado protege também o
  **corpo do e-mail** (que não passa pelo autoescape do template engine) e o
  **Admin** (embora o Django Admin também autoescape, a sanitização na
  gravação evita depender disso em qualquer superfície futura, ex.: uma
  API/export que reexiba `mensagem` sem escapar).
- **Trade-off:** `bleach` é uma dependência a mais; `nh3` (usado no
  `hub-ryan-morais`) seria uma alternativa mais moderna/rápida (Rust), mas
  trocar bibliotecas está fora do escopo desta sessão de modernização.

### ADR-03 — Rate limit ativado só após o envio (não a validação)

- **Decisão:** `cache.set(cache_key, True, 600)` roda **depois** de
  `send_mail()` suceder, não logo após `form.is_valid()`.
- **Porquê:** se o envio falhar, o visitante pode tentar de novo imediatamente
  em vez de ficar bloqueado por um erro que não foi culpa dele.
- **Trade-off:** um SMTP instável permite múltiplas tentativas seguidas (sem
  bloqueio), mas cada tentativa ainda passa pelo honeypot/sanitização.

### ADR-04 — Rate limit em memória (`LocMemCache`), não distribuído

- **Decisão:** `CACHES["default"]` usa `LocMemCache`.
- **Porquê:** deploy de processo único (PythonAnywhere); não há múltiplos
  workers/containers a sincronizar.
- **Trade-off:** um restart do processo zera todos os rate limits ativos;
  aceitável no volume de tráfego do projeto. Se o projeto crescer para
  múltiplos workers, precisaria migrar para Redis (mesma decisão documentada
  no `hub-ryan-morais`, spec 012, que já enfrentou esse limite).

## 6. Impacto e dependências

- Depende do `EMAIL_BACKEND`/`EMAIL_HOST_*` configurados em
  `portfolio/settings.py` (spec 003).
- `MaxLengthValidator` novo (`app_portfolio/models.py`) exigiu a migração
  `0022`.
- `disable_real_email` (fixture de teste) é uma dependência **inversa**: a
  suíte de testes depende dela para não tocar rede real; produção não é afetada.

## 7. Estratégia de testes

`TestSegurancaContato` cobre, com `EMAIL_BACKEND=locmem` e `MEDIA_ROOT`
temporário (fixtures autouse): sanitização XSS, bloqueio por rate limit
(HTML e AJAX/429), honeypot, envio de e-mail bem-sucedido (`mail.outbox`),
resposta AJAX de sucesso, falha simulada de SMTP (`unittest.mock.patch` em
`app_portfolio.views.send_mail`) e dados inválidos via AJAX (400). Não há
teste de integração real contra um servidor SMTP — está fora do escopo de
testes unitários/de view.
