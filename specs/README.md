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
novas**. As specs 001 a 003 foram reconstruídas por **engenharia reversa** de
um projeto já funcionando (exceção documentada na skill `/spec`), então já
nascem com `status: concluído` e `tasks.md` inteiramente `[x]`. A 004 nasceu de
uma auditoria de interface e foi escrita junto da correção, a pedido do Ryan
("aplique tudo conforme recomendado"), sem as pausas de aprovação entre as fases.

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
| 004 | [correcoes-de-interface](004-correcoes-de-interface/) | concluído | Correções da auditoria de interface: hero no celular, formulário com retorno, menu, contraste, avisos, fontes locais, páginas de erro e imagens novas |

> As specs 001 a 003 foram reconstruídas por **engenharia reversa** do código
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
- **`styles.css` e `main.js` sem Prettier** (spec [004](004-correcoes-de-interface/)):
  os dois arquivos usam 4 espaços e aspas simples. Rodar o Prettier (ou deixar o
  editor formatar ao salvar) reescreve o arquivo inteiro e apaga o diff real da
  mudança. Edite só o trecho.
- **Menu do celular: o corte de 768 px vale nos dois lados** (spec
  [004](004-correcoes-de-interface/), ADR-02): `MENU_DE_CELULAR` no `main.js` e o
  `@media (max-width: 768px)` do painel em `styles.css` precisam do mesmo valor.
  Com valores diferentes, o painel fica `inert` num tamanho em que o CSS o mostra,
  ou o contrário. O foco volta ao hambúrguer **antes** de o painel virar `inert`
  (elemento focado que fica inerte perde o foco); o `test_interface.py` guarda a
  ordem.
- **`test_interface.py` lê o CSS e o JavaScript como texto** (spec
  [004](004-correcoes-de-interface/)): o bloco `prefers-reduced-motion` tem de ser
  o último do `styles.css` (vence o hover e as animações de cima) e as regras são
  achadas pelo texto exato do seletor. Ao reordenar ou renomear no CSS, ajuste o
  teste junto; o teste que falha diz qual regra sumiu.
- **Dado opcional nunca vai sem `{% if %}`** (spec [004](004-correcoes-de-interface/),
  RF-01 e RF-10): `{{ perfil.curriculo.url }}` levanta `ValueError` sem arquivo e
  derruba a home com erro 500; `{{ projeto.link_github }}` vazio vira `href="None"`.
  Campo com `blank=True` pede a guarda no template e um teste com o campo vazio.
