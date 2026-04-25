![Portfólio Dinâmico com Django - Template Educativo para Portfólios](https://github.com/ryanvmorais/python-jogo-da-cobrinha/blob/main/assets/portfolio-fullstack-django.png?raw=true)

# 🌊 Portfólio Dinâmico com Django | Template Educativo para Portfólios

Este repositório contém um **Portfólio Profissional** desenvolvido com o framework Django. Embora se apresente visualmente como uma SPA (Single Page Application), o projeto foi construído como um sistema robusto, focando em **segurança avançada**, **otimização de banco de dados** e **arquitetura limpa**.

### 🎯 Objetivo do Projeto:
Demonstrar a aplicação de **boas práticas profissionais** de desenvolvimento Web, indo além do "CRUD básico". O foco aqui é oferecer um exemplo real de uma aplicação pronta para a internet, ensinando como implementar proteções contra bots, evitar ataques comuns e otimizar a performance do banco de dados de forma simples e didática.

---

### 📚 O que você vai encontrar neste projeto?

Este projeto foi estruturado para consolidar pilares fundamentais de engenharia de software:

* **Segurança Ofensiva e Defensiva:** Implementação de *Honeypot* (armadilha para bots), *Rate Limit* (limitação de envios por IP) e integração com `bleach` para sanitização de HTML.
* **Performance & Escala:** Uso de `select_related` e `prefetch_related` para mitigar o problema de consultas N+1, garantindo carregamento instantâneo.
* **DevOps Mindset:** Estrutura de dependências dividida entre `local`, `base` e `production`, além de configurações rigorosas de CSP (Content Security Policy) e HSTS.
* **Qualidade de Código:** Suíte de testes automatizados com `pytest` cobrindo fluxos de sucesso e tentativas de ataque.

---

### 🧠 Guia de Implementação: A Lógica por trás do Código:
Para quem está começando, o maior desafio não é decorar comandos do Django, mas entender a **montagem do raciocínio** de uma aplicação profissional. Confira os pilares da construção deste projeto:
1. **Arquitetura de Dados Relacional:** Em vez de textos soltos, utilizamos o **ORM do Django** para criar relacionamentos inteligentes. Por exemplo, um `Projeto` está ligado a uma `Categoria` e a várias `Tecnologias`. Isso permite que o banco de dados trabalhe por você, facilitando filtros e buscas.
2. **Otimização de Consultas (Performance):** Para evitar que o site fique lento, usamos um "truque sênior": o `select_related` e o `prefetch_related`. Eles reduzem o número de idas ao banco de dados, buscando todas as informações necessárias em uma única viagem, o que é crucial para manter a **Alta Performance**.
3. **Segurança Defensiva (Honeypot):** Para proteger o formulário de contato sem usar CAPTCHAs chatos, criamos uma "armadilha invisível". É um campo oculto que humanos não veem, mas robôs preenchem automaticamente. Se o campo for preenchido, o sistema identifica o bot e descarta o envio silenciosamente.
4. **Controle de Fluxo (Rate Limiting):** Para evitar ataques de spam (milhares de e-mails por segundo), implementamos uma trava no cache. O sistema monitora o IP do usuário e, após um envio com sucesso, bloqueia novas tentativas por 10 minutos, protegendo a integridade do seu servidor de e-mail.
5. **Sanitização de Conteúdo:** Nunca confiamos no que o usuário digita. Utilizamos a biblioteca `bleach` para "limpar" as mensagens recebidas, garantindo que qualquer tentativa de injetar scripts maliciosos (ataques XSS) seja neutralizada antes mesmo de chegar ao banco de dados.
6. **Blindagem do Navegador (CSP):** Configuramos o *Content Security Policy*. Isso é como um segurança na porta do site que diz ao navegador: "Só aceite estilos e scripts que venham deste próprio servidor". Isso impede que invasores injetem códigos externos no seu front-end.
7. **Dinamismo das Habilidades:** O sistema permite total controle sobre a exibição da barra de progresso das habilidades. Através do Painel Administrativo, você define o percentual (0 a 100) de habilidade em cada tecnologia. Caso não queira exibir a barra de progresso, basta desmarcar a seção `Exibir barras de progresso` no seu Perfil do Painel Administrativo (*Admin*) e clicar em salvar.
8. **URLs Amigáveis (Slugs):** Implementamos a geração automática de *Slugs*. Isso significa que o Django transforma títulos de projetos em links legíveis para humanos e motores de busca (SEO), evitando IDs numéricos confusos nas URLs.
9. **Ambiente de Produção Real:** O projeto não roda apenas no seu computador. Ele foi estruturado com variáveis de ambiente (`.env`) e configurações específicas para servidores (como o `WhiteNoise` para arquivos estáticos), garantindo que o deploy em plataformas como o **PythonAnywhere** seja suave e seguro.

---

### 🛠️ Tecnologias e Ferramentas:
Para garantir a melhor experiência de aprendizado e a execução correta de todos os recursos (como a limpeza de tela automática), o projeto utiliza as seguintes tecnologias:


| Ferramenta | Descrição | Badge |
| :--- | :--- | :--- |
| **Python 3.10+** | Linguagem base focada em legibilidade e eficiência no back-end. | ![Python - Linguagem de Programação](https://img.shields.io/badge/-Python-3776AB%3Fstyle%3Dflat%26logo%3Dpython?logo=python&logoColor=3776AB&logoSize=flat&color=F0F0F0) |
| **Django 4.2+** | Framework web "com baterias incluídas" utilizado para toda a lógica e ORM. | ![Django](https://img.shields.io/badge/Django-django?style=flat&logo=django&logoColor=%23092E20&color=F0F0F0) |
| **Pytest** | Framework de testes avançado para garantir a integridade de cada função. | ![Pytest](https://img.shields.io/badge/Pytest-pytest?style=flat&logo=pytest&logoColor=%230A9EDC&color=F0F0F0) |
| **Vanilla JS** | JavaScript puro (ES6+) para interações leves sem a carga de frameworks pesados. | ![JavaScript - Linguagem de Programação](https://img.shields.io/badge/-JavaScript-F7DF1E%3Fstyle%3Dflat%26logo%3Djavascript?style=flat&logo=javascript&logoColor=F7DF1E&logoSize=flat&color=F0F0F0) |
| **HTML5/CSS3** | Estrutura semântica e estilização moderna baseada em Flexbox e Grid. | ![HTML5/CSS3](https://img.shields.io/badge/HTML-html5?style=flat&logo=html5&logoColor=%23E34F26&color=F0F0F0) |
| **SQLite / Postgres** | Banco de dados relacional para persistência segura das informações. | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-postgresql?style=flat&logo=postgresql&logoColor=4169E1&color=F0F0F0) |

---

### ⚙️ Como rodar o projeto localmente:

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/ryanvmorais/django-fullstack-portfolio.git
    ```
2.  **Configure as variáveis de ambiente:**
    - Copie o arquivo `.env.example` para `.env` e insira suas chaves (SECRET_KEY, EMAIL_USER, etc).
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Execute as migrações e o servidor:**
    ```bash
    python manage.py migrate
    python manage.py runserver
    ```
> ⚠️ **Nota sobre o Formulário de Contato:** Para que o envio de e-mails funcione, você precisará de uma **"Senha de App"** do Google (caso use Gmail). Não utilize sua senha comum de login; o Google bloqueia essa conexão por segurança. Configure isso em *Segurança > Verificação em duas etapas > Senhas de App*.
---
### 📋 Atividades para praticar (Desafios de Evolução):

Para exercitar o que você aprendeu e dominar o Django, tente implementar estas novas funcionalidades:

1. **📊 Dashboard de Estatísticas (Admin Customizado):** No Django Admin, crie uma visualização que mostre quantos e-mails foram recebidos por dia.
   * **O Aprendizado:** Você aprenderá a manipular o `admin.ModelAdmin` e a trabalhar com agregações de banco de dados (`Count`, `Sum`).
2. **🌓 Chaveador de Tema (Dark/Light Mode):** Crie um botão no front-end que alterne entre o tema atual e uma versão clara do site, salvando a preferência no `localStorage` do navegador.
    * **O Aprendizado:** Fortalece o domínio de **Manipulação de DOM com Vanilla JS** e o uso de Variáveis CSS (*Design Tokens*).
3. **✉️ Notificações Push ou Telegram:** Altere a função de contato para que, além de enviar um e-mail, ela envie uma notificação para um bot do Telegram ou uma mensagem no Discord sempre que alguém preencher o formulário.
    * **O Aprendizado:** Você aprenderá a integrar o Django com **APIs externas** utilizando a biblioteca `requests`.
4. **📂 Filtros Dinâmicos de Projetos:** Implemente um sistema de busca na seção de projetos que filtre os resultados sem recarregar a página (usando AJAX).
    * **O Aprendizado:** Domínio de **Querysets** complexos e comunicação assíncrona entre o Front-end e o Back-end.

---

### 💡 Ficou com alguma dúvida ou tem sugestões?

Desenvolver sistemas robustos e seguros com Django envolve muitos detalhes técnicos, mas estou aqui para ajudar! Se você encontrou algum comportamento inesperado no código, teve dificuldades com as configurações de ambiente ou pensou em uma melhoria arquitetural que tornaria este projeto ainda mais didático:

*   **Abra uma [Issue](https://github.com/ryanvmorais/django-fullstack-portfolio/issues):** Clique no link e descreva sua dúvida ou sugestão. Esta é a melhor forma de construirmos um material de referência sólido para a comunidade e ajudarmos outros desenvolvedores que possam ter o mesmo questionamento!
*   **Me mande um E-mail:** Se preferir algo mais privado, pode me escrever em [**contato@ryanmorais.com.br**](mailto:contato@ryanmorais.com.br).

Ficarei muito feliz em acompanhar sua evolução com o framework Django e receber seu feedback para melhorar cada vez mais a qualidade deste material de estudo! 🤝

---

### ⚖️ Licença
Este projeto está sob a **Licença MIT**. Isso significa que você pode usar, copiar e modificar o código à vontade, inclusive para seus próprios projetos. Para mais detalhes, consulte o arquivo [LICENSE](LICENSE).