---
feature: Correções da auditoria de interface
status: concluído
data: 18/10/2026
relacionado:
  - 001-vitrine-portfolio
  - 002-formulario-contato
  - 003-configuracao-seguranca
origem: nova feature (auditoria de interface com a skill /auditoria-interface)
---

# Design — Correções da auditoria de interface

## 1. Visão geral

Quase tudo é CSS, marcação e JavaScript puro, no estilo que o projeto já tem
(tokens no `:root`, BEM, uma folha `styles.css`). Duas folhas e um punhado de
templates nascem: `fontes.css` (as fontes hospedadas) e as páginas de erro. O
`main.js` foi reescrito por funções com nome em português e um ponto de entrada
único (a skill `/estilo-arquivos`); o comportamento antigo (rolagem, filtros,
revelação ao rolar, envio por `fetch`) foi mantido, e o que mudou é o menu, os
avisos e o tratamento da resposta do servidor.

Dois pontos tocam o servidor: as mensagens da view de contato (a mesma frase em
JSON e em `django.contrib.messages`) e o modelo `Perfil`, que ganha quatro campos
opcionais de rede social.

## 2. Componentes

```
static/css/fontes.css        # novo: @font-face de Inter e JetBrains Mono (latin, variáveis)
static/css/styles.css        # tokens, hero, menu, avisos, erro, toque, movimento reduzido
static/fonts/                # novo: 2 woff2 + licenças OFL
static/js/main.js            # reescrito: menu com inert, filtros com aria-pressed, avisos, formulário
static/icons/                # favicon.webp (do emblema), default_perfil/projeto.webp, postgresql.svg
templates/base.html          # fontes locais, og:image absoluta, nomes acessíveis, títulos do rodapé em h2, avisos
templates/home.html          # currículo, link e capa opcionais; nomes; filtros; contato do perfil
templates/erro.html          # novo: base independente das páginas de erro
templates/{404,403,500}.html # novos: estendem o erro.html
app_portfolio/views.py       # MENSAGEM_* e messages nos fluxos HTML
app_portfolio/test_interface.py   # novo: um grupo de testes por requisito
portfolio/settings.py        # CSP sem Google Fonts
portfolio/urls.py            # /favicon.ico para um arquivo que existe
pyproject.toml               # override do mypy para o novo módulo de teste
```

## 3. Modelo de dados

Sem mudança. O `Perfil` e as migrações ficam como estavam (a última continua
sendo a `0022`).

## 4. Interfaces

Respostas JSON da view `home` (cabeçalho `X-Requested-With: XMLHttpRequest`):

| Situação | Status | `message` |
|---|---|---|
| Enviado | 200 | `MENSAGEM_ENVIADO` ("Mensagem enviada!") |
| Limite de 10 minutos | 429 | `MENSAGEM_LIMITE_ENVIO` |
| Formulário inválido | 400 | `MENSAGEM_DADOS_INVALIDOS` |
| Falha de e-mail | 500 | `MENSAGEM_FALHA_ENVIO` |

O fluxo HTML usa as mesmas constantes em `messages.success` e `messages.error`.
O `main.js` mostra `message` de toda resposta que não seja `ok` com
`status === 'success'`.

## 5. Decisões técnicas (ADRs)

### ADR-01 — Hero: texto primeiro e bloco decorativo fora do celular

- **Decisão:** abaixo de 1024 px o bloco de código passa a vir depois do texto
  (some o `order: -1`); some de vez abaixo de 640 px e em celular deitado; os
  espaços encolhem e as três estatísticas ficam numa linha (grade de 3 colunas);
  `min-height: 100svh`.
- **Alternativas:** (a) só esconder o bloco no celular; (c) manter o bloco no
  celular, depois das estatísticas.
- **Porquê:** a opção (a) ainda deixava as estatísticas fora da tela; a (c) deixava
  o hero com ~960 px, rolagem a mais para um enfeite. A escolhida (b) foi medida em
  10 tamanhos: título e botões cabem em todo celular em pé, e o hero inteiro cabe
  de 390 x 844 para cima.
- **Trade-off:** no celular o visitante não vê o bloco de código; em 360 x 640 as
  estatísticas ficam ~60 px abaixo da tela.

### ADR-02 — Menu do celular: `inert` e altura dinâmica

- **Decisão:** o painel é `inert` enquanto fechado, só no celular (por
  `matchMedia`, mesmo ponto de corte do CSS); ao abrir, o resto da página fica
  inerte, o foco vai ao primeiro link, `aria-expanded` acompanha, e o Esc (ou o
  botão de fechar) devolve o foco ao hambúrguer antes de o painel voltar a ser
  `inert`. O painel usa `100dvh`.
- **Alternativas:** `visibility: hidden` no painel (exigiria acompanhar a
  transição); `display: none` (perde a animação de entrada).
- **Porquê:** `right: -100%` só tira o painel da tela, não do Tab nem do leitor de
  tela. O `inert` resolve os dois e não interfere na transição.
- **Trade-off:** sem JavaScript o painel não abre de qualquer jeito, então o
  `inert` (feito por JavaScript) não muda nada para quem não tem JS.

### ADR-03 — Contraste por token

- **Decisão:** `--color-gray-400` sobe de #64748b para #8393aa (4,67:1 sobre o
  cartão, o pior fundo); `--color-gray-500` fica só como cor de borda.
- **Alternativas:** corrigir cada componente; usar o `--color-gray-300`.
- **Porquê:** 20 dos 22 textos reprovados usavam o mesmo token; um valor novo
  corrige todos e mantém a hierarquia (cinza de apoio abaixo do cinza do texto).
- **Trade-off:** o texto de apoio fica um pouco mais claro e perto do corpo.

### ADR-04 — Redes do rodapé fixas

- **Decisão:** o rodapé continua com as seis redes escritas no `base.html`, iguais
  para todo perfil. Só os títulos viram `h2` (RF-12).
- **Alternativas:** (a) quatro campos opcionais no `Perfil`, com migração, para
  mostrar só as redes preenchidas (foi a primeira versão desta spec); (b) tirar
  as redes que o perfil não tem.
- **Porquê:** o projeto é educativo e o rodapé é um exemplo de layout: quem usa o
  template troca os endereços no HTML. Quatro campos e uma migração por causa de
  links de exemplo pesam mais que o ganho. Foi decisão do Ryan, depois de ver a
  alternativa (a) pronta.
- **Trade-off:** os links levam à página inicial de cada rede, não a um perfil
  real. O `base.html` avisa isso num comentário.

### ADR-05 — Fontes hospedadas, só latin e variáveis

- **Decisão:** Inter (400 a 700) e JetBrains Mono (400 a 500) em `static/fonts/`,
  um arquivo variável de cada, subconjunto latin, `font-display: swap`; preload
  só da Inter; a CSP perde `fonts.googleapis.com` e `fonts.gstatic.com`.
- **Alternativas:** manter o Google Fonts; pacote npm (exigiria build).
- **Porquê:** sem requisição de terceiros (LGPD), sem CSS externo bloqueando a
  primeira pintura e uma superfície de CSP menor. É o caminho que o blog culinário
  já seguiu.
- **Trade-off:** 80 KB de fontes no repositório e atualização manual.

### ADR-06 — Um componente de aviso para os dois fluxos

- **Decisão:** `.notification` (com `.notifications` como região `role="status"`)
  serve ao aviso criado pelo `main.js` e às mensagens do Django no `base.html`;
  o aviso de erro leva `role="alert"` e fica até ser fechado; o de sucesso some
  em 6 s.
- **Alternativas:** manter o aviso inline do JavaScript e deixar o `.toast` do
  `base.html` sem estilo.
- **Porquê:** o `.toast` nunca teve CSS: no fluxo sem JavaScript o aviso saía como
  texto solto depois do rodapé. Um componente só evita dois visuais para a mesma
  coisa.
- **Trade-off:** o aviso de erro não some sozinho.

### ADR-07 — Alvos de toque só em tela de toque

- **Decisão:** os controles pequenos (filtros, links do rodapé e do contato, ícones
  sociais) chegam a 44 px dentro de `@media (pointer: coarse)`; o menu do celular
  tem 44 px por ser uma tela estreita.
- **Alternativas:** 44 px sempre.
- **Porquê:** com mouse, 44 px em links de rodapé alonga a página sem ganho.
- **Trade-off:** quem usa o computador com tela de toque e `pointer: fine` mantém o
  tamanho compacto (ainda acima dos 24 px da WCAG 2.2).

### ADR-08 — Capas de projeto decorativas

- **Decisão:** `alt=""` na capa do projeto.
- **Alternativas:** um campo `imagem_alt` no modelo.
- **Porquê:** as capas são ilustrações abstratas e o título está ao lado.
- **Trade-off:** se uma capa passar a trazer informação, o campo precisa nascer.

### ADR-09 — Filtros e botão do GitHub continuam em 14 px

- **Decisão:** os chips de filtro e o botão "Ver no GitHub" ficam em `--fs-sm`
  (14 px), mesma família do corpo (16 px).
- **Alternativas:** subir todos a 16 px.
- **Porquê:** são controles secundários e compactos; a medição de proporções só
  os marca pelo tamanho (`fonte_do_corpo`), com a fonte, o centro do rótulo e a
  altura corretos.
- **Trade-off:** a ferramenta continua apontando 11 ocorrências, aceitas.

### ADR-10 — Páginas de erro independentes

- **Decisão:** `erro.html` é um documento completo que não herda o `base.html`;
  `404.html`, `403.html` e `500.html` só preenchem blocos. Sem JavaScript e sem
  contexto.
- **Alternativas:** estender o `base.html`.
- **Porquê:** o `base.html` lê o perfil e tem âncoras `#seção` que, numa página de
  erro, apontam para o lugar errado; o 500 acontece justamente quando algo falhou.
- **Trade-off:** o erro não tem o menu da home.

### ADR-11 — Imagens: nomes de SEO e recortes fixos

- **Decisão:** capas de projeto em 1280 x 800 (16:10, o `aspect-ratio` do cartão),
  foto de perfil em 960 x 1200 (4:5), emblema de reserva em 1280 x 800, favicon
  quadrado de 256 px tirado do emblema (`</>`); todos em WebP qualidade 80 (88 no
  favicon), com nomes como `plataforma-de-ecommerce-loja-virtual-holografica-com-fones-neon.webp`.
  `default_perfil.webp` e `default_projeto.webp` seguem com esse nome, que o
  template referencia.
- **Alternativas:** manter os nomes antigos (`plataforma_de_ecommerce.webp`).
- **Porquê:** o nome do arquivo entra no SEO de imagem; recortar na proporção da
  tela evita que o `object-fit: cover` corte o assunto.
- **Trade-off:** trocar uma imagem pelo admin deixa o arquivo antigo na pasta
  `media/` (o projeto não usa `django-cleanup`).

## 6. Impacto e dependências

- Nenhuma migração: o deploy não precisa de `migrate` por causa desta spec.
- A CSP fica mais estreita; nenhuma outra página carregava fonte externa.
- Sem dependência nova.

## 7. Estratégia de testes

pytest com o cliente do Django. O HTML da home é renderizado com perfis que
variam um campo opcional por vez; o CSS e o JavaScript são lidos como texto e
conferidos por regra (contraste calculado dos tokens, blocos `@media`, marcadores
de comportamento); o e-mail e a mídia seguem isolados como nas specs 001 e 002.
Cada teste foi provado desfazendo a correção (43 mutações, todas pegas). A
verificação em navegador real não entra no pytest.
