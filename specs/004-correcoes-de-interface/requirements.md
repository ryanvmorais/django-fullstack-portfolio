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

# Requisitos — Correções da auditoria de interface

> Escrita depois da auditoria, a pedido do Ryan ("aplique todas as correções,
> inclusive as sugestões, conforme recomendado"). Cada requisito nasceu de um
> achado medido em Chrome real (10 tamanhos de celular, 768 e 1280 px, axe-core
> 4.14.0, Tab, formulário e dados opcionais). Os números "antes" abaixo são
> dessa medição.

## 1. Contexto e problema

A home é uma página única com tema escuro "Tech Deep Ocean". A auditoria de
18/10/2026 achou 24 problemas (5 altos, 11 médios, 8 baixos ou sugestões) e
a correção revelou mais alguns (favicon, avisos sem estilo, imagens padrão).
Os principais:

- a home dava **erro 500** quando o perfil não tinha currículo;
- o **hero** tinha 1.165 px de altura em todo celular, com o bloco de código
  decorativo na frente do nome e os botões a 766 px da primeira tela;
- o formulário **não mostrava nada** quando o servidor devolvia erro (limite de
  10 minutos, dados inválidos, falha de e-mail);
- o menu do celular deixava 6 paradas de Tab fora da tela;
- 22 textos tinham contraste entre 2,18:1 e 3,8:1;
- o resto: nomes acessíveis, estados dos filtros, movimento reduzido, textos
  provisórios, arquivos que não existem (`avatar_padrao.webp`,
  `favicon.png`), fontes pelo Google e imagens com a estrela do Gemini.

## 2. Objetivos

- Corrigir os 24 achados e os extras, cada um com um teste que falha se a
  correção for desfeita.
- Título, botões e números do hero na primeira tela do celular.
- Nenhuma página quebra por dado opcional vazio (currículo, foto, link do
  GitHub, redes sociais).
- Trocar as imagens com a marca d'água do Gemini por imagens novas, com nome
  de arquivo de SEO.

## 3. Não-objetivos

- Trocar a identidade visual (ciano sobre azul-marinho, botões em degradê, bloco
  de código decorativo no desktop).
- Introduzir framework de CSS ou etapa de build: o projeto continua CSS e
  JavaScript puros.
- Os pontos de infraestrutura que a auditoria só viu de passagem: o
  `STATICFILES_STORAGE` (ignorado pelo Django 6.1; o nome certo é `STORAGES`) e
  a compressão do WhiteNoise ficam fora desta spec.
- Leitor de tela de verdade, Safari no iPhone e produção (PythonAnywhere): não
  verificados.

## 4. Requisitos funcionais e critérios de aceite

### RF-01 — Home sem currículo

- **Given** um `Perfil` sem arquivo de currículo
  **When** a home é aberta
  **Then** ela responde 200 e o botão "Download CV" não aparece.
- **Given** um `Perfil` com currículo
  **When** a home é aberta
  **Then** o botão aparece e aponta para o arquivo.

### RF-02 — O hero cabe na primeira tela do celular

- **Given** um celular em pé de 390 px de largura ou mais
  **When** a home abre
  **Then** título, descrição, os dois botões e as três estatísticas ficam
  dentro da altura visível, e o hero inteiro cabe.
- **Given** qualquer celular em pé (360 px ou mais)
  **When** a home abre
  **Then** o título e os dois botões ficam dentro da altura visível.
- **Given** uma tela de até 640 px, ou deitada com menos de 500 px de altura
  **When** o hero é desenhado
  **Then** o bloco de código decorativo não aparece; entre 641 e 1024 px ele vem
  depois do texto, nunca antes.

### RF-03 — O visitante vê o resultado do envio

- **Given** o servidor responde 400, 429 ou 500 a um envio por JavaScript
  **When** a resposta chega
  **Then** um aviso de erro mostra a frase completa que o servidor mandou, e o
  aviso fica até ser fechado.
- **Given** um envio sem JavaScript (POST comum)
  **When** ele é aceito, barrado pelo limite, inválido ou falha no e-mail
  **Then** a página mostra um aviso com a mesma frase, no mesmo componente.
- **Given** o limite de 10 minutos
  **When** o servidor responde 429
  **Then** a frase é "Você já enviou uma mensagem recentemente. Aguarde 10
  minutos para enviar outra.", sem reticências.

### RF-04 — Menu do celular e foco por teclado

- **Given** o menu do celular fechado
  **When** o visitante percorre a página com Tab
  **Then** nenhum link do painel recebe foco (o painel é `inert`); no desktop o
  menu nunca é inerte.
- **Given** o botão do hambúrguer
  **When** o menu abre
  **Then** `aria-expanded` vira `true` e o foco vai para o primeiro link;
  enquanto aberto, o resto da página fica inerte.
- **Given** o menu aberto
  **When** o visitante aperta Esc ou o botão de fechar
  **Then** o menu fecha e o foco volta ao hambúrguer; clique em link ou fora do
  painel fecha sem devolver o foco.
- **Given** qualquer elemento focado por teclado
  **When** ele não é um campo do formulário
  **Then** tem um anel de foco de 2 px ciano (`:focus-visible`).

### RF-05 — Contraste do texto

- **Given** qualquer texto de apoio sobre os quatro fundos escuros
  **When** o contraste é calculado
  **Then** é de pelo menos 4,5:1 (`--color-gray-400` passa de #64748b para
  #8393aa); o copyright e o texto de exemplo dos campos usam esse token.

### RF-06 — Avisos acessíveis

- **Given** um aviso de sucesso, erro ou informação
  **When** ele aparece
  **Then** o texto tem 4,5:1 ou mais sobre o fundo (`#047857`, `#b91c1c`,
  `#1d4ed8`), vive numa região `role="status"`, o de erro leva `role="alert"` e
  o botão de fechar tem 44 x 44 px e o nome "Fechar aviso".

### RF-07 — Barras de habilidade com nome

- **Given** o perfil com "Exibir barras de progresso" ligado
  **When** a home é lida por leitor de tela
  **Then** cada `role="progressbar"` tem `aria-label` com o nome da habilidade.

### RF-08 — Movimento reduzido

- **Given** o sistema pede "reduzir movimento"
  **When** a página carrega ou o visitante usa âncoras e passa o mouse
  **Then** não há animação contínua (bloco do hero, seta "Explorar"), rolagem
  suave, elevação ao passar o mouse nem revelação com deslocamento, inclusive na
  rolagem feita por JavaScript.

### RF-09 — Foto padrão do perfil

- **Given** um `Perfil` sem foto
  **When** a home abre
  **Then** a imagem de reserva é `static/icons/default_perfil.webp`, que existe
  (antes: `avatar_padrao.webp`, 404), em 4:5 e com menos de 150 KiB.

### RF-10 — Link do GitHub opcional e com nome próprio

- **Given** um projeto sem `link_github`
  **When** a home abre
  **Then** o botão não aparece (antes: `href="None"`).
- **Given** um projeto com link
  **When** a home é lida por leitor de tela
  **Then** o link se chama "Ver no GitHub do projeto <título>".

### RF-11 — Nome acessível começa pelo texto visível

- **Given** o logo ("<Nome />") e o indicador "Explorar"
  **When** um comando de voz diz o texto que aparece
  **Then** o `aria-label` de cada um começa por esse texto ("Nome, voltar ao
  início"; "Explorar: rolar para a seção Sobre").

### RF-12 — Títulos sem pulo de nível

- **Given** o rodapé
  **When** a estrutura de títulos é lida
  **Then** "Links Rápidos" e "Redes Sociais" são `h2` (antes `h4` logo depois de
  `h2`), com o mesmo visual.

### RF-13 — Filtros com estado e campos com autocomplete

- **Given** os filtros de projeto
  **When** o visitante escolhe um
  **Then** só ele fica com `aria-pressed="true"` e uma região viva anuncia
  quantos projetos ficaram.
- **Given** os campos de nome e e-mail
  **When** o celular os preenche
  **Then** declaram `autocomplete="name"` e `autocomplete="email"`.

### RF-14 — Sem texto provisório: contato e rodapé saem do perfil

- **Given** o perfil com LinkedIn e GitHub preenchidos
  **When** a home abre
  **Then** o cartão mostra o endereço do próprio perfil, sem `https://` nem
  `www.` (antes: "/in/seu_usuario"), com `rel="noopener"`; o cartão some quando o
  campo está vazio.
- **Given** as redes do rodapé (Facebook, Instagram, LinkedIn, X, TikTok, GitHub)
  **When** a home abre
  **Then** só aparecem as preenchidas no perfil, e a coluna "Redes Sociais" some
  se nenhuma estiver.
- **Given** o logo do rodapé
  **When** o visitante clica
  **Then** vai para `#home` (antes `href="#"`).

### RF-15 — Transições listadas e altura dinâmica

- **Given** qualquer regra de transição do CSS
  **When** o arquivo é lido
  **Then** lista as propriedades (nenhum `transition: all`).
- **Given** o painel do menu e o hero
  **When** a altura da tela é a do celular com a barra do navegador
  **Then** usam `100dvh` e `100svh`, com `100vh` de reserva.

### RF-16 — Botões com a mesma altura

- **Given** "Ver Projetos" e "Entrar em Contato"
  **When** são medidos
  **Then** têm a mesma altura (57,6 px; antes 57,6 e 61,6 px).

### RF-17 — Fontes hospedadas no projeto

- **Given** qualquer página
  **When** o navegador monta o `<head>`
  **Then** nenhuma requisição vai ao Google Fonts: Inter e JetBrains Mono vêm de
  `static/fonts/`, com `font-display: swap`, preload da Inter e as licenças OFL
  ao lado; a CSP não libera mais `fonts.googleapis.com` nem `fonts.gstatic.com`.

### RF-18 — Alvos de toque

- **Given** uma tela de toque (`pointer: coarse`)
  **When** os controles são medidos
  **Then** filtros, links do rodapé e do contato e ícones sociais têm 44 px; no
  celular, o hambúrguer, o fechar e os links do painel também.

### RF-19 — Páginas de erro do projeto

- **Given** `DEBUG=False`
  **When** o endereço não existe (404), a ação não é permitida (403) ou o servidor
  falha (500)
  **Then** o visitante vê uma página em português, com `lang`, `viewport`,
  `<main>`, um `h1`, `noindex` e um botão de volta, e o 500 não consulta o banco.

### RF-20 — Imagem de compartilhamento e ícone da aba

- **Given** o perfil com foto
  **When** a página é compartilhada
  **Then** a `og:image` tem endereço absoluto (esquema e host).
- **Given** qualquer página
  **When** o navegador procura o ícone
  **Then** o `<link rel="icon">` declara `image/webp`, `/favicon.ico` redireciona
  para um arquivo que existe (antes: `favicon.png`, 404) e o ícone é quadrado,
  sem a marca do Gemini, com menos de 20 KiB (antes: 1024 x 1024, 516 KiB).

### RF-21 — Capas de projeto decorativas

- **Given** a capa de um projeto
  **When** a página é lida por leitor de tela
  **Then** a imagem tem `alt=""` (o título ao lado já nomeia o projeto).

### RF-22 — Sem código nem CSS sobrando

- **Given** o CSS e o JavaScript
  **When** são lidos
  **Then** não restam as regras `.project-card__overlay` e `__link`, a animação
  das barras por `data-progress`, a digitação, o parallax, o preloader nem o
  alternador `.keyboard-nav`.

### RF-23 — Quebra de linha

- **Given** títulos e parágrafos
  **When** o texto quebra
  **Then** `h1` a `h4` usam `text-wrap: balance` e `p` e `li` usam `pretty`
  (antes: 2 palavras sozinhas na última linha).

### RF-24 — Rodapé alinhado e ícone legível

- **Given** as três colunas do rodapé
  **When** a página é vista no desktop
  **Then** começam na mesma altura.
- **Given** o ícone do PostgreSQL sobre o chip escuro
  **When** o contraste é calculado
  **Then** é de pelo menos 4,5:1 (antes 2,65:1).

## 5. Requisitos não-funcionais

- **RNF-01 — Sem dependência nova.** Nada de biblioteca nem etapa de build; as
  fontes são arquivos estáticos e o JavaScript continua puro.
- **RNF-02 — Tudo por tokens.** Cores novas (avisos, cinza legível) entram como
  variáveis no `:root`, não como valores soltos.
- **RNF-03 — Imagens leves.** Capas em 1280 x 800 (16:10), foto de perfil em 960
  x 1200 (4:5), tudo em WebP qualidade 80 e abaixo de 150 KiB; nome do arquivo
  com palavras-chave (SEO).
- **RNF-04 — Estilo preservado.** O `styles.css` mantém a indentação e as aspas
  de sempre: o diff mostra só o que mudou.

## 6. Perguntas em aberto / decisões resolvidas

1. **Redes do rodapé (RF-14):** viram campos opcionais do `Perfil` (migração
   `0023`), em vez de sair do rodapé ou ficar fixas. Reversível: é decisão do
   Ryan (ver ADR-04).
2. **Filtros e botão do GitHub em 14 px:** continuam menores que o corpo (16 px),
   na mesma família. A `/auditoria-interface` os sinaliza como `fonte_do_corpo`;
   foram tratados como chips e botões secundários (ver ADR-09).
3. **Imagens:** o Ryan gerou as novas no ChatGPT a partir dos prompts da
   auditoria. O banco local não existia (o projeto só guarda dados no servidor);
   foi criado um `db.sqlite3` de demonstração, ignorado pelo Git, com as seis
   capas e a foto novas. Em produção, as imagens entram pelo admin.

## 7. Testes

Um arquivo, `app_portfolio/test_interface.py`, com um grupo por requisito:

- **HTML renderizado** pelo cliente de teste: home com e sem currículo, foto,
  link e redes; filtros, campos, rodapé, `og:image`, favicon.
- **Respostas da view de contato:** frases dos erros 400, 429 e 500 em JSON, e os
  avisos do fluxo sem JavaScript.
- **Páginas de erro:** 404 pela rota, 403 e 500 pelos handlers (o 500 sem consulta
  ao banco).
- **CSS e JavaScript lidos como texto:** contraste calculado dos tokens, blocos
  `@media`, ausência de `transition: all`, marcadores de comportamento do menu,
  dos avisos e da rolagem.
- **Arquivos estáticos:** fontes, licenças, favicon quadrado e leve, imagens
  padrão em 4:5 e 16:10.

Cada correção foi provada desfazendo-a: 43 mutações, todas pegas por algum teste.
O navegador real (axe-core, Tab, medidas do hero) fica fora do pytest.
