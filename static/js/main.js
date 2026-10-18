// ---------------------------------------------------------------------------
// Portfólio: JavaScript da home
// JavaScript puro, sem framework e sem build. Roda no fim do <body>; o
// ponto de entrada fica no fim do arquivo, depois de todas as funções.
// ---------------------------------------------------------------------------

(function () {
    'use strict';

    // -----------------------------------------------------------------------
    // CONSTANTES E ELEMENTOS
    // -----------------------------------------------------------------------

    // Mesmo ponto de corte do CSS: abaixo dele o menu vira um painel lateral
    // (@media (max-width: 768px) em styles.css).
    const MENU_DE_CELULAR = window.matchMedia('(max-width: 768px)');

    // "Reduzir movimento" do sistema (spec 004, RF-08). O CSS cobre as
    // animações; aqui só a rolagem feita por JavaScript.
    const MENOS_MOVIMENTO = window.matchMedia('(prefers-reduced-motion: reduce)');

    // Tempo que o aviso de sucesso fica na tela, em ms. O de erro fica até
    // ser fechado: some sozinho em 5 s e o visitante perderia o que corrigir.
    const TEMPO_DO_AVISO = 6000;

    const header = document.getElementById('header');
    const navMenu = document.getElementById('nav-menu');
    const navToggle = document.getElementById('nav-toggle');
    const navClose = document.getElementById('nav-close');
    const navLinks = document.querySelectorAll('.nav__link');
    const backToTop = document.getElementById('back-to-top');
    const contactForm = document.getElementById('contact-form');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const projectCards = document.querySelectorAll('.project-card');
    const projectsStatus = document.getElementById('projects-status');
    const sections = document.querySelectorAll('section[id]');

    // Conteúdo que fica inerte enquanto o menu do celular está aberto, para o
    // Tab não sair do painel para a página que está atrás dele.
    const conteudoDeFundo = [
        document.getElementById('main-content'),
        document.querySelector('.footer'),
        backToTop,
    ].filter(Boolean);


    // -----------------------------------------------------------------------
    // ROLAGEM
    // O CSS já desliga o scroll-behavior suave com "reduzir movimento"; esta
    // função faz o mesmo para o window.scrollTo, que ignora o CSS quando
    // recebe o valor 'smooth' (RF-08).
    // -----------------------------------------------------------------------
    function comportamentoDeRolagem() {
        return MENOS_MOVIMENTO.matches ? 'auto' : 'smooth';
    }


    // -----------------------------------------------------------------------
    // MENU DO CELULAR
    // O painel fica fora da tela por right: -100%, o que não o tira do Tab nem
    // do leitor de tela. Por isso ele é inerte enquanto fechado (RF-04);
    // no desktop o menu é a barra de sempre e nunca recebe inert.
    // -----------------------------------------------------------------------
    function menuEstaAberto() {
        return navMenu.classList.contains('show');
    }

    function sincronizarMenu() {
        const bloqueado = MENU_DE_CELULAR.matches && !menuEstaAberto();
        navMenu.inert = bloqueado;
    }

    function abrirMenu() {
        if (!navMenu) {
            return;
        }
        // O inert sai antes do foco: elemento inerte não aceita foco.
        navMenu.inert = false;
        navMenu.classList.add('show');
        navToggle.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
        conteudoDeFundo.forEach((elemento) => {
            elemento.inert = true;
        });
        navLinks[0].focus({ preventScroll: true });
    }

    /**
     * Fecha o painel do celular.
     *
     * @param {{devolverFoco?: boolean}} [opcoes] - devolverFoco leva o foco de
     *   volta ao botão do menu (Esc e botão de fechar). Clique em link ou fora
     *   do painel não devolve: a página navega ou o visitante foi para outro lugar.
     */
    function fecharMenu({ devolverFoco = false } = {}) {
        if (!navMenu) {
            return;
        }
        navMenu.classList.remove('show');
        navToggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
        conteudoDeFundo.forEach((elemento) => {
            elemento.inert = false;
        });
        // O foco volta ao botão ANTES de o painel virar inert: um elemento
        // focado que fica inerte perde o foco para o <body>.
        if (devolverFoco) {
            navToggle.focus();
        }
        sincronizarMenu();
    }

    function iniciarMenu() {
        sincronizarMenu();
        MENU_DE_CELULAR.addEventListener('change', () => {
            // Ao passar para o desktop com o painel aberto, fecha sem mexer no foco.
            if (!MENU_DE_CELULAR.matches && menuEstaAberto()) {
                fecharMenu();
            }
            sincronizarMenu();
        });

        if (navToggle) {
            navToggle.addEventListener('click', abrirMenu);
        }
        if (navClose) {
            navClose.addEventListener('click', () => fecharMenu({ devolverFoco: true }));
        }
        navLinks.forEach((link) => {
            link.addEventListener('click', () => fecharMenu());
        });

        // Clique fora do painel fecha sem roubar o foco
        document.addEventListener('click', (e) => {
            if (menuEstaAberto() && !navMenu.contains(e.target) && !navToggle.contains(e.target)) {
                fecharMenu();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && menuEstaAberto()) {
                fecharMenu({ devolverFoco: true });
            }
        });
    }


    // -----------------------------------------------------------------------
    // EFEITOS DO SCROLL
    // Cabeçalho com fundo mais forte, botão "voltar ao topo" e link ativo do
    // menu. O listener usa requestAnimationFrame para não rodar a cada pixel.
    // -----------------------------------------------------------------------
    function atualizarLinkAtivo() {
        const scrollY = window.scrollY;

        sections.forEach((section) => {
            const alturaDaSecao = section.offsetHeight;
            const topoDaSecao = section.offsetTop - 100;
            const idDaSecao = section.getAttribute('id');

            if (scrollY >= topoDaSecao && scrollY < topoDaSecao + alturaDaSecao) {
                navLinks.forEach((link) => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${idDaSecao}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }

    function tratarScroll() {
        const scrollY = window.scrollY;

        if (header) {
            header.classList.toggle('scrolled', scrollY > 50);
        }
        if (backToTop) {
            backToTop.classList.toggle('show', scrollY > 500);
        }
        atualizarLinkAtivo();
    }

    function iniciarScroll() {
        let aguardando = false;
        window.addEventListener('scroll', () => {
            if (!aguardando) {
                window.requestAnimationFrame(() => {
                    tratarScroll();
                    aguardando = false;
                });
                aguardando = true;
            }
        });
        tratarScroll();
    }


    // -----------------------------------------------------------------------
    // ÂNCORAS
    // Os links #seção rolam descontando a altura do cabeçalho fixo.
    // -----------------------------------------------------------------------
    function iniciarAncoras() {
        document.querySelectorAll('a[href^="#"]').forEach((ancora) => {
            ancora.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
                if (!href || href === '#') {
                    return;
                }
                const alvo = document.querySelector(href);
                if (!alvo) {
                    return;
                }
                e.preventDefault();
                const alturaDoCabecalho = header ? header.offsetHeight : 0;
                window.scrollTo({
                    top: alvo.offsetTop - alturaDoCabecalho,
                    behavior: comportamentoDeRolagem(),
                });
            });
        });
    }


    // -----------------------------------------------------------------------
    // FILTROS DE PROJETO
    // O botão ativo ganha a classe .active (visual) e aria-pressed (leitor de
    // tela); a região #projects-status anuncia quantos projetos ficaram (RF-13).
    // -----------------------------------------------------------------------
    function filtrarProjetos(categoria, rotulo) {
        let visiveis = 0;

        projectCards.forEach((card) => {
            const mostrar = categoria === 'all' || card.getAttribute('data-category') === categoria;
            card.hidden = !mostrar;
            if (mostrar) {
                visiveis += 1;
                card.style.animation = 'fadeInUp 0.5s ease forwards';
            }
        });

        if (projectsStatus) {
            const plural = visiveis === 1 ? 'projeto' : 'projetos';
            projectsStatus.textContent = categoria === 'all'
                ? `Mostrando todos os ${visiveis} ${plural}.`
                : `Mostrando ${visiveis} ${plural} em ${rotulo}.`;
        }
    }

    function iniciarFiltros() {
        filterBtns.forEach((btn) => {
            btn.addEventListener('click', function () {
                filterBtns.forEach((b) => {
                    b.classList.remove('active');
                    b.setAttribute('aria-pressed', 'false');
                });
                this.classList.add('active');
                this.setAttribute('aria-pressed', 'true');
                filtrarProjetos(this.getAttribute('data-filter'), this.textContent.trim());
            });
        });
    }


    // -----------------------------------------------------------------------
    // REVELAR AO ROLAR
    // Cartões e blocos nascem com .reveal (invisíveis) e ganham .active ao
    // entrar na tela. Com "reduzir movimento", o CSS os deixa sempre visíveis.
    // -----------------------------------------------------------------------
    function iniciarRevelar() {
        const elementos = document.querySelectorAll('.project-card, .skills__category, .contact__card');

        const observador = new IntersectionObserver((entradas) => {
            entradas.forEach((entrada) => {
                if (entrada.isIntersecting) {
                    entrada.target.classList.add('reveal', 'active');
                    observador.unobserve(entrada.target);
                }
            });
        }, { threshold: 0.1 });

        elementos.forEach((el) => {
            el.classList.add('reveal');
            observador.observe(el);
        });
    }


    // -----------------------------------------------------------------------
    // AVISOS
    // Mostra o resultado do envio do formulário. Os avisos moram numa região
    // role="status" (o leitor de tela anuncia); o de erro leva role="alert" e
    // fica até ser fechado. O visual está em .notification, no styles.css (RF-03).
    // -----------------------------------------------------------------------
    function obterContainerDeAvisos() {
        let container = document.querySelector('.notifications');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notifications';
            container.setAttribute('role', 'status');
            document.body.appendChild(container);
        }
        return container;
    }

    function fecharNotificacao(aviso) {
        aviso.classList.add('notification--leaving');
        // 300 ms = duração de slideOutRight no CSS
        setTimeout(() => aviso.remove(), 300);
    }

    function mostrarNotificacao(mensagem, tipo = 'info') {
        const container = obterContainerDeAvisos();
        container.querySelectorAll('.notification').forEach((antigo) => antigo.remove());

        const aviso = document.createElement('div');
        aviso.className = `notification notification--${tipo}`;
        if (tipo === 'error') {
            aviso.setAttribute('role', 'alert');
        }

        const texto = document.createElement('span');
        texto.className = 'notification__message';
        texto.textContent = mensagem;

        const fechar = document.createElement('button');
        fechar.type = 'button';
        fechar.className = 'notification__close';
        fechar.setAttribute('aria-label', 'Fechar aviso');
        fechar.textContent = '×';
        fechar.addEventListener('click', () => fecharNotificacao(aviso));

        aviso.append(texto, fechar);
        container.appendChild(aviso);

        if (tipo !== 'error') {
            setTimeout(() => {
                if (aviso.isConnected) {
                    fecharNotificacao(aviso);
                }
            }, TEMPO_DO_AVISO);
        }
    }


    // -----------------------------------------------------------------------
    // FORMULÁRIO DE CONTATO
    // Envia por fetch com o token CSRF. A view responde JSON com status e
    // message; todo status que não seja sucesso (400, 429, 500) vira aviso de
    // erro com a frase que o servidor mandou (RF-03).
    // -----------------------------------------------------------------------
    function iniciarFormulario() {
        if (!contactForm) {
            return;
        }

        contactForm.addEventListener('submit', function (e) {
            e.preventDefault();

            // 1. Validação básica no navegador, antes do fetch
            const obrigatorios = this.querySelectorAll('input[required], textarea[required]');
            const tudoPreenchido = [...obrigatorios].every((campo) => campo.value.trim());
            if (!tudoPreenchido) {
                mostrarNotificacao('Preencha todos os campos para enviar a mensagem.', 'error');
                return;
            }

            // 2. Envio
            const dadosDoFormulario = new FormData(this);
            const botaoEnviar = this.querySelector('button[type="submit"]');
            const textoOriginal = botaoEnviar.innerHTML;

            botaoEnviar.disabled = true;
            botaoEnviar.innerHTML = '<span>Enviando...</span>';

            fetch(this.action || window.location.href, {
                method: 'POST',
                body: dadosDoFormulario,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
            })
                .then(async (resposta) => {
                    // Corpo que não é JSON (página de erro do servidor) vira null
                    const dados = await resposta.json().catch(() => null);
                    if (resposta.ok && dados && dados.status === 'success') {
                        mostrarNotificacao(dados.message, 'success');
                        contactForm.reset();
                    } else {
                        mostrarNotificacao(
                            (dados && dados.message) || 'Não foi possível enviar agora. Tente novamente em alguns minutos.',
                            'error',
                        );
                    }
                })
                .catch(() => {
                    mostrarNotificacao('Erro ao conectar com o servidor.', 'error');
                })
                .finally(() => {
                    botaoEnviar.disabled = false;
                    botaoEnviar.innerHTML = textoOriginal;
                });
        });
    }


    // -----------------------------------------------------------------------
    // PONTO DE ENTRADA ÚNICO
    // -----------------------------------------------------------------------
    function iniciar() {
        iniciarMenu();
        iniciarScroll();
        iniciarAncoras();
        iniciarFiltros();
        iniciarRevelar();
        iniciarFormulario();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();
