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

# Tasks — Correções da auditoria de interface

## Etapa 1 — Dados e servidor

- [x] `app_portfolio/models.py`, `admin.py` e migração `0023`: quatro campos
      opcionais de rede social no `Perfil`, com bloco próprio no admin. — RF-14, ADR-04
- [x] `app_portfolio/views.py`: constantes `MENSAGEM_*`, mesma frase em JSON e em
      `messages`, e avisos nos fluxos HTML (sucesso, limite, inválido, falha). — RF-03, ADR-06
- [x] `portfolio/settings.py`: CSP sem `fonts.googleapis.com` e `fonts.gstatic.com`. — RF-17, ADR-05
- [x] `portfolio/urls.py`: `/favicon.ico` redireciona para o `favicon.webp`, com
      caminho absoluto. — RF-20
- [x] Portão de qualidade. — 13 testes originais verdes, `manage.py check` sem problemas

## Etapa 2 — Folhas de estilo e fontes

- [x] `static/fonts/` e `static/css/fontes.css`: Inter e JetBrains Mono
      hospedadas (variáveis, latin), com as licenças OFL. — RF-17, ADR-05
- [x] `static/css/styles.css` (tokens): `--color-gray-400` em #8393aa; cores dos
      avisos; copyright e texto de exemplo dos campos no token legível. — RF-05, RF-06, ADR-03
- [x] `static/css/styles.css` (hero e menu): texto primeiro, bloco de código fora
      do celular, estatísticas em grade, `svh` e `dvh`. — RF-02, RF-15, ADR-01, ADR-02
- [x] `static/css/styles.css` (componentes): avisos, páginas de erro, botões de
      mesma altura, rodapé alinhado, alvos de toque, `text-wrap`, `:focus-visible`,
      `transition` listada e CSS sem uso removido. — RF-04, RF-06, RF-15, RF-16, RF-18, RF-19, RF-22, RF-23, RF-24, ADR-06, ADR-07
- [x] `static/css/styles.css` (fim do arquivo): bloco de movimento reduzido. — RF-08
- [x] Portão de qualidade. — o diff do `styles.css` ficou em +313 / −69 linhas,
      sem reformatar o resto do arquivo

## Etapa 3 — JavaScript

- [x] `static/js/main.js`: reescrito por funções, com ponto de entrada único; menu
      com `inert`, foco e Esc; filtros com `aria-pressed` e região viva; avisos
      criados com `role`; erro do servidor mostrado; rolagem por
      `comportamentoDeRolagem()`; código sem uso removido. — RF-03, RF-04, RF-06, RF-08, RF-13, RF-22, ADR-02, ADR-06
- [x] Portão de qualidade. — `main.js` sem erro de sintaxe; verificado no Chrome
      (menu, Esc, formulário com 200 e 429)

## Etapa 4 — Templates

- [x] `templates/base.html`: fontes locais e preload, `og:image` absoluta, tipo do
      favicon, `aria-label` do logo, estado do hambúrguer, rodapé com `h2`, redes do
      perfil e avisos no componente novo. — RF-03, RF-04, RF-11, RF-12, RF-14, RF-17, RF-20
- [x] `templates/home.html`: currículo, foto e link opcionais; nome do link do
      GitHub; capa decorativa; barras com nome; filtros com estado; `autocomplete`;
      contato e rodapé vindos do perfil. — RF-01, RF-07, RF-09, RF-10, RF-11, RF-13, RF-14, RF-21
- [x] `templates/erro.html`, `404.html`, `403.html` e `500.html`. — RF-19, ADR-10
- [x] Portão de qualidade. — axe-core 4.14.0: 0 violações em 390 e 1280 px; Tab sem
      parada invisível; 0 palavras órfãs

## Etapa 5 — Imagens

- [x] Seis capas de projeto (1280 x 800, WebP q80, 43 a 81 KiB) com nomes de SEO,
      em `media/projetos/`, e o banco local de demonstração criado com elas. — RNF-03, ADR-11
- [x] Retrato do perfil (960 x 1200, 102 KiB) em `media/perfil/` e em
      `static/icons/default_perfil.webp`. — RF-09, ADR-11
- [x] `static/icons/default_projeto.webp` (emblema `</>`, sem texto, 30 KiB; antes
      622 KiB) e `favicon.webp` (do emblema, 256 px, 10 KiB; antes 516 KiB, com a
      marca do Gemini). — RF-20, ADR-11
- [x] `static/icons/tech/postgresql.svg` em azul claro (6,0:1 sobre o chip). — RF-24
- [x] Portão de qualidade. — nenhuma imagem do repositório tem mais a marca do Gemini

## Etapa 6 — Testes e verificação

- [x] `app_portfolio/test_interface.py`: um grupo de testes por requisito (HTML
      renderizado, view, páginas de erro, CSS e JS como texto, arquivos estáticos);
      `pyproject.toml` com o override do mypy para o módulo. — RF-01 a RF-24
- [x] Prova por mutação: 43 correções desfeitas, uma por vez. — 43 de 43 pegas
      (duas sobreviveram na primeira rodada e os testes foram reforçados)
- [x] Verificação no Chrome: hero em 10 tamanhos, contraste, Tab, menu, formulário,
      proporções e as páginas de erro com `DEBUG=False`. — RF-02, RF-03, RF-04, RF-05
- [x] Portão de qualidade completo. — 88 passed (13 originais + 75 novos);
      `ruff`, `black --check` e `mypy` verdes; `manage.py check` sem problemas

## Etapa 7 — Documentação

- [x] Esta spec (`004-correcoes-de-interface/`) e o índice em `specs/README.md`. — origem
- [x] `CLAUDE.md`, `README.md` e `docs/stack.md`: fontes locais, avisos, páginas
      de erro, redes do perfil, testes de interface e as regras que não podem
      regredir. — RNF-01
- [x] Portão de qualidade. — todo `RF-NN` e `ADR-NN` citado existe nos
      requisitos e no design

### Medida do hero (Chrome real, altura visível estimada)

| Tela | Visível | Antes (botões / estatísticas) | Depois (botões / estatísticas) |
|---|---|---|---|
| 360 x 640 | 560 | 901 / 1101 | 512 / 626 |
| 390 x 844 | 664 | 901 / 1101 | 492 / 605 |
| 412 x 915 | 760 | 901 / 1101 | 540 / 653 |
| 430 x 932 | 760 | 901 / 1101 | 553 / 641 |
| 480 x 1000 | 840 | 901 / 1101 | 593 / 681 |
| 844 x 390 (deitado) | 340 | 820 / 940 | 400 / 488 |
