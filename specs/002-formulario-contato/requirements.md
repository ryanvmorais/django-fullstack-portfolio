---
feature: Formulário de contato (anti-spam, sanitização e notificação por e-mail)
status: concluído
data: 11/09/2026
relacionado:
  - 001-vitrine-portfolio
  - 003-configuracao-seguranca
origem: engenharia reversa do código existente (app_portfolio)
---

# Requisitos — Formulário de Contato

> Reconstruído por engenharia reversa. Cobertura em `app_portfolio/tests.py`
> (`TestSegurancaContato`). A auditoria de segurança desta sessão (ver
> `specs/003-configuracao-seguranca/`) corrigiu duas falhas encontradas nesta
> feature antes da documentação: chamadas SMTP reais durante os testes, e
> ausência de limite de tamanho no campo `mensagem`.

## 1. Contexto e problema

O formulário de contato da home precisa aceitar mensagens de visitantes reais
sem virar um vetor de spam, XSS ou abuso de custo (envio de e-mail é
limitado/pago em muitos provedores), e sem exigir CAPTCHA de terceiros.

## 2. Objetivos

- Registrar toda mensagem recebida no banco (`MensagemContato`), mesmo que o
  e-mail de notificação falhe.
- Bloquear bots simples sem fricção para o usuário real (sem CAPTCHA).
- Impedir XSS armazenado via campo `mensagem`.
- Suportar tanto submissão HTML tradicional quanto AJAX (JSON).
- Notificar o administrador por e-mail a cada mensagem válida.

## 3. Não-objetivos

- CAPTCHA (reCAPTCHA/hCaptcha) — resolvido só com honeypot + rate limit.
- Fila assíncrona de e-mail — o envio é síncrono, dentro do ciclo de request.
- Anexos ou campos além de nome/e-mail/assunto/mensagem.

## 4. Personas

- **Visitante** — preenche o formulário para contatar o desenvolvedor.
- **Bot/spammer** — tenta submeter em massa ou injetar HTML malicioso.
- **Administrador** — recebe o e-mail e consulta o histórico no Admin
  (`MensagemContatoAdmin`, campos somente leitura).

## 5. Requisitos funcionais e critérios de aceite

### RF-01 — Honeypot

- **Given** o campo oculto `honeypot` (invisível via CSS, `tabindex="-1"`)
  **When** um POST chega com `honeypot` preenchido
  **Then** a view redireciona para `home` silenciosamente, sem salvar nada e
  sem processar o restante do formulário.

### RF-02 — Rate limit por IP

- **Given** um envio bem-sucedido
  **When** o mesmo IP (`REMOTE_ADDR`) tenta enviar de novo dentro de 10 minutos
  **Then** a segunda tentativa é bloqueada: HTML recebe uma mensagem de erro
  via `django.contrib.messages` e redirect; AJAX recebe HTTP 429 com JSON
  `{"status": "error", ...}`.
- **Given** a chave de cache `contact_limit_{ip}` expirada
  **Then** o IP volta a poder enviar normalmente.

### RF-03 — Sanitização XSS do campo mensagem

- **Given** uma `mensagem` contendo `<script>...</script>` ou outra tag HTML
  **When** o formulário é válido
  **Then** `bleach.clean(mensagem, tags=[], strip=True)` remove todas as tags
  antes de `MensagemContato` ser salvo — o banco nunca guarda HTML bruto do
  campo mensagem.
- **Nota:** apenas `mensagem` é sanitizada; `nome` e `assunto` não passam por
  `bleach` (são `CharField`, exibidos apenas em contexto de texto simples no
  Admin e no corpo em texto puro do e-mail — sem `autoescape off`/`|safe` em
  nenhum template).

### RF-04 — Limite de tamanho da mensagem

- **Given** um payload de `mensagem` maior que 5000 caracteres
  **When** o formulário é validado
  **Then** `MaxLengthValidator(5000)` no model rejeita o envio (`form.is_valid()`
  retorna `False`).
- **Corrigido nesta sessão** (auditoria de segurança, achado BAIXA): antes,
  `mensagem` era um `TextField` sem limite, permitindo payloads arbitrariamente
  grandes por envio a cada janela de rate limit.

### RF-05 — Notificação por e-mail

- **Given** uma mensagem válida e não bloqueada por rate limit
  **When** ela é salva
  **Then** `send_mail()` envia um e-mail em texto simples (assunto
  `"Novo Contato: {assunto}"`, corpo com nome/e-mail/mensagem) para
  `settings.EMAIL_HOST_USER`, e o rate limit do IP é ativado por 600s
  **somente após** o envio ter sido tentado com sucesso.
- **Given** falha no envio (SMTP indisponível, credenciais inválidas)
  **Then** a exceção é capturada e logada (`logger.exception`); a mensagem já
  salva no banco não é perdida; AJAX recebe HTTP 500 com JSON de erro; HTML
  não recebe feedback de erro específico (limitação conhecida — ver
  "Perguntas em aberto").

### RF-06 — Respostas híbridas HTML/AJAX

- **Given** o header `X-Requested-With: XMLHttpRequest`
  **Then** toda resposta (sucesso, bloqueio, dados inválidos, erro de envio)
  é `JsonResponse` com `status` (`"success"`/`"error"`) e código HTTP
  apropriado (200/429/400/500).
- **Given** ausência desse header
  **Then** o fluxo usa `redirect`/`django.contrib.messages` (navegação HTML
  tradicional, com `follow=True` nos testes para seguir o redirect).

### RF-07 — Histórico somente leitura no Admin

- **Given** o Admin de `MensagemContato`
  **Then** todos os campos de conteúdo (`nome`, `email`, `assunto`,
  `mensagem`, `data_envio`) são `readonly_fields` — o Admin serve para
  consulta e marcação de `lida`, nunca para editar o conteúdo recebido.

## 6. Requisitos não-funcionais

- **RNF-01 (Isolamento de testes):** a suíte nunca deve depender de rede real.
  Corrigido nesta sessão: `disable_real_email` (fixture autouse) força
  `EMAIL_BACKEND` para `locmem` durante os testes — antes, `send_mail()`
  tentava conectar ao SMTP real do Gmail a cada teste que passava pelo POST
  de contato.
- **RNF-02 (Resiliência):** falha no envio de e-mail nunca deve impedir o
  registro da mensagem no banco (a ordem no código é: salvar primeiro, depois
  tentar enviar).
- **RNF-03 (CSP):** o formulário não depende de `'unsafe-inline'` em
  `script-src` — corrigido nesta sessão (ver spec 003).

## 7. Perguntas em aberto

- Falha de envio de e-mail no fluxo **HTML** (não-AJAX) não gera nenhum
  feedback visível ao usuário — ele vê a página normal sem saber se o e-mail
  foi enviado. Não corrigido nesta sessão (mudança de comportamento, não bug
  de segurança).
- O rate limit é por `REMOTE_ADDR` puro, sem suporte a `X-Forwarded-For` —
  correto para o modelo de deploy atual (PythonAnywhere expõe o IP real do
  visitante), mas quebraria atrás de um proxy que não repassa o IP original.
