---
feature: Configuração e postura de segurança (settings, CSP, admin, deploy)
status: concluído
data: 11/09/2026
relacionado:
  - 002-formulario-contato
origem: engenharia reversa do código existente (portfolio/settings.py)
---

# Design — Configuração e Segurança

## 1. Visão geral

Um único `portfolio/settings.py`, dividido em 5 blocos numerados por
comentário (ambiente/segredos, middlewares/apps, estáticos/mídia, segurança
avançada condicionada a `DEBUG`, serviços externos). Toda diferença entre dev
e produção é resolvida por variável de ambiente, nunca por um segundo arquivo
de settings.

## 2. Componentes

| Componente | Arquivo | Responsabilidade |
|---|---|---|
| Bloco 1 (env/segredos) | `portfolio/settings.py:19-47` | `SECRET_KEY`, `DEBUG`, `ADMIN_URL_PATH`, `ALLOWED_HOSTS` |
| `MIDDLEWARE` | `portfolio/settings.py:60-70` | Ordem: Security → WhiteNoise → Session → Common → CSRF → Auth → Messages → XFrameOptions → CSP |
| Bloco 4 (segurança avançada) | `portfolio/settings.py:124-147` | HSTS, cookies seguros, SSL redirect — só com `DEBUG=False` |
| `django-csp` | `portfolio/settings.py:130-135` | Diretivas `CSP_*` |
| `portfolio/urls.py` | raiz | Monta `admin.site.urls` em `settings.ADMIN_URL_PATH` |
| `whitenoise` | `MIDDLEWARE` + `STATICFILES_STORAGE` | Serve e comprime estáticos sem servidor dedicado |
| `.env.example` | raiz | Documenta cada variável exigida, sem valores reais |

## 3. Modelo de dados

Não aplicável — esta spec cobre configuração, não models.

## 4. Interfaces

Variáveis de ambiente consumidas por `settings.py` (documentadas em
`.env.example`):

| Variável | Padrão | Obrigatória |
|---|---|---|
| `SECRET_KEY` | — | Sim (levanta `ValueError` se ausente) |
| `DEBUG` | `False` | Não |
| `ADMIN_URL` | `admin/` | Não |
| `ALLOWED_HOSTS` | `*` (dev) / vazio (prod) | Recomendada em produção |
| `EMAIL_USER` / `EMAIL_PASS` | — | Só para o formulário de contato funcionar (spec 002) |

## 5. Decisões técnicas (ADRs)

### ADR-01 — Um único `settings.py` para dev e produção

- **Decisão:** sem `settings/base.py` + `settings/dev.py` + `settings/prod.py`
  (padrão comum em projetos maiores); tudo em um arquivo, ramificado por
  `if not DEBUG:`.
- **Alternativas:** múltiplos módulos de settings (usado no `hub-ryan-morais`
  via `settings_test.py` para os testes).
- **Porquê:** projeto de escala pequena, um único app — a divisão em módulos
  adicionaria indireção sem benefício proporcional.
- **Trade-off:** os testes rodam contra o mesmo `settings.py` de produção,
  então precisam neutralizar manualmente o que `DEBUG=False` ligaria
  (`disable_ssl_redirect`, ver spec 002) em vez de herdar de um settings de
  teste dedicado.

### ADR-02 — CSP com `'unsafe-inline'` em `style-src`, mas não em `script-src`

- **Decisão (corrigida nesta sessão):** `CSP_SCRIPT_SRC = ("'self'",)` — sem
  `'unsafe-inline'`. `CSP_STYLE_SRC` mantém `'unsafe-inline'` porque
  `home.html` usa 2 atributos `style=""` inline (barra de progresso de
  habilidades, com largura dinâmica vinda do banco).
- **Porquê:** antes da correção, `script-src` também tinha `'unsafe-inline'`
  sem necessidade real (nenhum `<script>` inline em nenhum template) — isso
  anulava boa parte do valor do CSP como defesa contra XSS.
- **Alternativas futuras:** nonce por request (como o `hub-ryan-morais`, spec
  010) resolveria também o `style-src`, mas exigiria mover a largura da barra
  de progresso para uma custom property CSS lida via `data-*` — fora do
  escopo desta sessão.

### ADR-03 — Ofuscação da URL do Admin como defesa em profundidade

- **Decisão:** `ADMIN_URL_PATH` via `.env`, sem valor fixo `admin/` em
  produção.
- **Porquê:** reduz o volume de tentativas de brute-force automatizado (bots
  que varrem `/admin/` por padrão), sem substituir autenticação real.
- **Trade-off:** segurança por obscuridade — não impede um atacante
  direcionado que descubra a URL por outro meio (linkado, vazado em log,
  etc.). Complementar, não substituto, de uma senha forte.

### ADR-04 — Sem 2FA no Admin (diferente do `hub-ryan-morais`)

- **Decisão:** autenticação do Admin é usuário/senha padrão do Django.
- **Porquê:** escopo e público do projeto (portfólio pessoal, um único
  administrador) não justificam a complexidade de `django-two-factor-auth` +
  `django-axes` que o Hub aplica (spec 012) — decisão explícita de escala, não
  descuido.

## 6. Impacto e dependências

- `django-csp`, `whitenoise`, `python-dotenv`, `certifi` são as dependências
  diretas desta spec (declaradas em `pyproject.toml`).
- Qualquer novo `<script>`/`<style>` inline em template exige revisar
  `CSP_SCRIPT_SRC`/`CSP_STYLE_SRC` antes de shippar — regressão silenciosa
  senão (o CSP bloqueia sem erro visível no servidor, só no console do
  navegador).

## 7. Estratégia de testes

Não há teste automatizado desta spec na suíte `pytest` — a verificação é
manual (`manage.py check --deploy` + auditoria de segurança desta sessão:
`pip-audit`, `semgrep`, `detect-secrets`, revisão OWASP). `disable_ssl_redirect`
(spec 002) existe justamente porque os testes de view rodam contra este
`settings.py` sem um settings de teste dedicado.
