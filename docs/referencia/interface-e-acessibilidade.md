# Interface e acessibilidade (spec 004): regras que não podem regredir

Mapa: vai mexer no hero, no menu do celular, em cores, avisos, movimento, fontes, imagens ou nas páginas de erro? Leia antes.

A home foi auditada em Chrome real (10 tamanhos de celular, 768 e 1280 px,
axe-core, Tab, formulário) e corrigida na spec `004-correcoes-de-interface`. As
regras que ficaram, e que um ajuste "inofensivo" desfaria:

- **Hero no celular:** título, botões e estatísticas cabem na primeira tela. O
  bloco de código (`.hero__visual`, decorativo, `aria-hidden`) vem **depois** do
  texto e some abaixo de 640 px e em celular deitado; as três estatísticas ficam
  numa grade de 3 colunas.
- **Menu do celular:** o painel `#nav-menu` é `inert` enquanto fechado (só no
  celular, por `matchMedia` no `main.js`); ao abrir, o foco vai ao primeiro link e
  o resto da página fica inerte; Esc e o botão de fechar devolvem o foco ao
  hambúrguer. **O corte de 768 px é o mesmo no JS e no CSS.**
- **Contraste:** o texto de apoio usa `--color-gray-400` (#8393aa, 4,67:1 no pior
  fundo). `--color-gray-500` é só cor de borda, nunca de texto.
- **Avisos:** um componente só, `.notification`, para o `main.js` (AJAX) e para as
  `messages` do `base.html` (sem JavaScript). O de erro leva `role="alert"` e fica
  até ser fechado.
- **Movimento reduzido:** o bloco `prefers-reduced-motion` é o **último** do
  `styles.css` e a rolagem do JS passa por `comportamentoDeRolagem()`. Nada de
  `behavior: 'smooth'` solto nem de `transition: all`.
- **Fontes:** Inter e JetBrains Mono em `static/fonts/` (`fontes.css`); o Google
  Fonts não está mais na CSP nem nos templates.
- **Imagens:** capas de projeto em 1280 x 800 (16:10), foto de perfil em 960 x 1200
  (4:5), WebP q80, nome de arquivo com palavras-chave. As imagens de reserva
  (`default_perfil.webp`, `default_projeto.webp`) e o `favicon.webp` ficam em
  `static/icons/` e não têm a marca d'água do Gemini.
- **Páginas de erro:** `404.html`, `403.html` e `500.html` estendem o `erro.html`,
  independente do `base.html` (sem banco, sem JavaScript). Só aparecem com
  `DEBUG=False`; com `DEBUG=True` o Django mostra a página técnica.
