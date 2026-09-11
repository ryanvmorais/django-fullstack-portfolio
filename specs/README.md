# Specs — Spec-Driven Development

Esta pasta contém as **especificações** do projeto no padrão *spec-driven
development*. Specs são Markdown puro, versionado no Git — **agnósticas de
ferramenta**: servem para você, para o CI e para qualquer IA. A skill que as
opera (`/spec`) vive em `~/.claude/skills/`, mas as specs em si independem dela.

## Por que specs

Escrever o **quê/porquê** (requirements) e o **como** (design) antes de codar
evita retrabalho e deixa decisões rastreáveis. Para o código que já existe,
specs por **engenharia reversa** documentam o sistema de forma viva e servem
de referência para os próximos projetos.

## Estrutura

```
specs/
  README.md                      # este arquivo (metodologia + índice)
  NNN-nome-da-feature/
    requirements.md              # o quê e por quê + critérios de aceite (Given/When/Then)
    design.md                    # arquitetura, modelo de dados, decisões (ADRs), trade-offs
    tasks.md                     # quebra executável, rastreada aos requisitos
```

### Convenções

- **Pasta por feature**, prefixada por número sequencial: `001-vitrine-portfolio`, `002-formulario-contato`…
- **Nome** em kebab-case, curto e estável.
- **Frontmatter** em cada documento:
  ```yaml
  ---
  feature: <título legível>
  status: rascunho | aprovado | em andamento | concluído
  data: DD/MM/AAAA
  relacionado: [outras specs]      # opcional
  origem: <nova feature | engenharia reversa do código existente (...)>
  ---
  ```
- **Critérios de aceite** em **Given/When/Then** (BDD) — testáveis.
- **Decisões técnicas** no `design.md` como mini-ADRs: *Decisão · Alternativas ·
  Porquê · Trade-off*.
- **Rastreabilidade**: cada tarefa em `tasks.md` referencia o(s) requisito(s)
  que satisfaz (`— RF-05`).

## Workflow (4 fases com portões de aprovação)

```
requirements.md  ──(aprovação)──▶  design.md  ──(aprovação)──▶  tasks.md  ──(aprovação)──▶  implementação
```

Não se avança de fase sem o "ok" humano — esse é o fluxo para **features
novas**. As três specs atuais foram reconstruídas por **engenharia reversa** de
um projeto já funcionando (exceção documentada na skill `/spec`), então já
nascem com `status: concluído` e `tasks.md` inteiramente `[x]`.

## Como usar (com Claude Code)

| Comando | Ação |
|---|---|
| `/spec nova <nome>` | Cria `specs/NNN-<nome>/` e escreve `requirements.md`; para para aprovação |
| `/spec design` | Após requisitos aprovados, escreve `design.md`; para para aprovação |
| `/spec tasks` | Após design aprovado, escreve `tasks.md`; para para aprovação |
| `/spec implementar` | Executa as tarefas em ordem, marcando `[x]` e rodando os portões de qualidade |
| `/spec status` | Resume o estado de todas as specs (lê o frontmatter) |

Sem o Claude Code, os mesmos documentos guiam qualquer dev ou IA — são só Markdown.

## Índice de specs

| # | Spec | Status | Descrição |
|---|---|---|---|
| 001 | [vitrine-portfolio](001-vitrine-portfolio/) | concluído | Perfil, projetos, tecnologias, habilidades e estatísticas na home |
| 002 | [formulario-contato](002-formulario-contato/) | concluído | Honeypot, rate limit, sanitização XSS e notificação por e-mail |
| 003 | [configuracao-seguranca](003-configuracao-seguranca/) | concluído | Settings, CSP, admin ofuscado, hardening de produção e CI de segurança |

> As três specs foram reconstruídas por **engenharia reversa** do código
> existente, nesta sessão de modernização (2026-09-11), que também incluiu uma
> auditoria de segurança completa e a migração de `pip` para `uv`.

## Notas de manutenção (gotchas)

Configurações sutis em que uma alteração "inofensiva" pode reintroduzir um
problema já corrigido. Leia antes de mexer nos arquivos citados.

- **CSP e scripts/estilos inline** (spec [003](003-configuracao-seguranca/)):
  `CSP_SCRIPT_SRC` em `portfolio/settings.py` **não** tem `'unsafe-inline'` —
  foi removido de propósito porque nenhum template usa `<script>` inline.
  Adicionar um `<script>` inline em qualquer template quebra silenciosamente
  (o navegador só bloqueia no console, o servidor não acusa erro). Se
  precisar de script inline, use nonce (ver ADR-02 da spec 003) em vez de
  reintroduzir `'unsafe-inline'`.
- **`disable_real_email` em `app_portfolio/tests.py`** (spec
  [002](002-formulario-contato/)): é `autouse=True` de propósito. Removê-la
  (ou criar um novo teste em outro módulo sem essa fixture) faz o teste tentar
  uma conexão SMTP real contra o Gmail configurado em `settings.py` — lento,
  dependente de rede, e capaz de enviar e-mail de verdade se o `.env` local
  tiver credenciais reais.
- **`mensagem` com `MaxLengthValidator(5000)`** (spec
  [002](002-formulario-contato/)): o limite é aplicado só via `full_clean()`
  do `ModelForm`. Criar um `MensagemContato` diretamente por código
  (`.objects.create(...)`, como em fixtures de teste) **não** aciona o
  validador — é esperado, não um bug a corrigir.
