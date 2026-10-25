"""
🌱 COMANDO: DADOS DE DEMONSTRAÇÃO (semear_dados_demo)
🎯 Objetivo: Preencher o banco com dados fictícios para auditar a Home e desenvolver.

Um banco vazio devolve uma Home sem projetos, habilidades nem estatísticas, e as
métricas do Lighthouse ficam enganosas. O Lighthouse CI
(``.github/workflows/lighthouse.yml``) roda este comando antes de subir o servidor.

O comando é idempotente (rodar duas vezes não duplica nada), recusa rodar com
``DEBUG=False`` (são dados de mentira, nunca de produção) e gera as imagens com o
Pillow, para o CI não depender de rede nem de arquivos no repositório.

Uso::

    uv run python manage.py semear_dados_demo
"""

from __future__ import annotations

import io
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

from app_portfolio.models import (
    CategoriaHabilidade,
    CategoriaProjeto,
    Estatistica,
    Habilidade,
    Perfil,
    Projeto,
    Tecnologia,
)

# --- 1. DADOS DE DEMONSTRAÇÃO ---

# Paleta (topo, base) dos gradientes que fazem as vezes de foto. Geradas aqui, com o
# Pillow, para o comando não depender de rede (o Lighthouse CI roda isolado).
CORES = [
    ("#2563eb", "#0f172a"),
    ("#0d9488", "#042f2e"),
    ("#9333ea", "#1e1b4b"),
]

# Ícones que já existem em static/icons/tech/.
TECNOLOGIAS = [
    ("Python", "python.svg"),
    ("Django", "django.svg"),
    ("PostgreSQL", "postgresql.svg"),
    ("Docker", "docker.svg"),
]

# (nome, slug): o slug é o que os projetos abaixo usam para escolher a categoria.
CATEGORIAS_PROJETO = [("Web", "web"), ("API", "api")]

# (título, slug da categoria): a descrição é a mesma para todos.
PROJETOS = [
    ("Loja virtual", "web"),
    ("API de pedidos", "api"),
    ("Painel de métricas", "web"),
]

# Categoria de habilidade -> (ícone de static/icons/, habilidades com o progresso).
HABILIDADES = {
    "Back-end": ("server.svg", [("Python", 90), ("Django", 85), ("PostgreSQL", 75)]),
    "Infraestrutura": ("cloud.svg", [("Docker", 70), ("Linux", 65), ("CI/CD", 60)]),
}

# (título, legenda, destaque_sobre): a legenda quebra linha no "\n", como no admin.
ESTATISTICAS = [
    ("5+", "Anos de\nexperiência", True),
    ("30+", "Projetos\nentregues", False),
    ("15+", "Clientes\natendidos", False),
]


class Command(BaseCommand):
    """
    Cria perfil, projetos, tecnologias, habilidades e estatísticas de demonstração.

    Idempotente e restrito a ``DEBUG=True``; ver a docstring do módulo.

    Uso::

        uv run python manage.py semear_dados_demo
    """

    help = "Cria dados de demonstração (só com DEBUG=True) para auditorias e testes."

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Cria cada grupo de dados e informa o total ao final.

        Fluxo:
            1. Recusa rodar se ``DEBUG`` estiver desligado.
            2. Cria o perfil, se ainda não houver um.
            3. Cria as tecnologias e os projetos com imagem.
            4. Cria as habilidades e as estatísticas.
            5. Imprime o total de projetos e habilidades.

        Args:
            *args (Any): Argumentos posicionais (não utilizados).
            **options (Any): Argumentos nomeados do parser (não utilizados).

        Raises:
            CommandError: Se ``settings.DEBUG`` for falso.
        """
        if not settings.DEBUG:
            raise CommandError(
                "semear_dados_demo só roda com DEBUG=True: são dados de "
                "demonstração, nunca de produção."
            )

        self._perfil()
        tecnologias = self._tecnologias()
        self._projetos(tecnologias)
        self._habilidades()
        self._estatisticas()
        self.stdout.write(
            self.style.SUCCESS(
                f"Dados de demonstração prontos: {Projeto.objects.count()} projetos, "
                f"{Habilidade.objects.count()} habilidades."
            )
        )

    # --- 2. UTILITÁRIOS ---

    @staticmethod
    def _imagem(
        nome: str, largura: int, altura: int, indice: int
    ) -> ContentFile[bytes]:
        """
        Gera um gradiente JPEG para usar como imagem de um ``ImageField``.

        Os modelos convertem para WebP no ``save()``, como com um upload real.

        Args:
            nome (str): Nome do arquivo.
            largura (int): Largura em pixels.
            altura (int): Altura em pixels.
            indice (int): Posição na paleta ``CORES`` (dá a volta ao passar do fim).

        Returns:
            ContentFile[bytes]: Arquivo em memória, pronto para atribuir ao campo.
        """
        topo, base = CORES[indice % len(CORES)]
        gradiente = Image.linear_gradient("L").resize((largura, altura))
        imagem = ImageOps.colorize(gradiente, black=base, white=topo)
        buffer = io.BytesIO()
        imagem.save(buffer, format="JPEG", quality=80)
        return ContentFile(buffer.getvalue(), name=nome)

    # --- 3. CRIAÇÃO DOS DADOS ---

    def _perfil(self) -> None:
        """Cria o perfil (nome, contatos e foto) se ainda não houver um."""
        if Perfil.objects.exists():
            return
        perfil = Perfil.objects.create(
            nome="Maria Souza",
            cargo="Desenvolvedora Full Stack",
            bio="Desenvolvo aplicações web do banco de dados à interface.\n\n"
            "Gosto de código simples, testado e bem documentado.",
            bio_curta="Aplicações web do banco de dados à interface.",
            anos_experiencia=5,
            mostrar_progresso=True,
            email_contato="maria@example.com",
            telefone="+55 11 90000-0000",
            localizacao="São Paulo, Brasil",
            status_trabalho="Disponível para projetos",
            formacao="Análise e Desenvolvimento de Sistemas",
            link_linkedin="https://www.linkedin.com/in/maria-souza-demo",
            link_github="https://github.com/maria-souza-demo",
        )
        perfil.foto.save(
            "demo-perfil.jpg", self._imagem("demo-perfil.jpg", 800, 800, 0)
        )

    @staticmethod
    def _tecnologias() -> list[Tecnologia]:
        """
        Cria as tecnologias exibidas na Home.

        Returns:
            list[Tecnologia]: As tecnologias, na ordem de ``TECNOLOGIAS``.
        """
        return [
            Tecnologia.objects.get_or_create(
                nome=nome,
                defaults={"icone": icone, "mostrar_no_home": True, "ordem": ordem},
            )[0]
            for ordem, (nome, icone) in enumerate(TECNOLOGIAS)
        ]

    def _projetos(self, tecnologias: list[Tecnologia]) -> None:
        """
        Cria as categorias de projeto e os projetos com imagem e tecnologias.

        Args:
            tecnologias (list[Tecnologia]): Tecnologias associadas a cada projeto.
        """
        categorias = {
            slug: CategoriaProjeto.objects.get_or_create(
                slug=slug, defaults={"nome": nome}
            )[0]
            for nome, slug in CATEGORIAS_PROJETO
        }
        for ordem, (titulo, slug) in enumerate(PROJETOS):
            projeto, novo = Projeto.objects.get_or_create(
                titulo=titulo,
                defaults={
                    "categoria_projeto": categorias[slug],
                    "descricao": "Projeto de demonstração com autenticação, "
                    "testes automatizados e deploy contínuo.",
                    "link_github": "https://github.com/maria-souza-demo/demo",
                    "ordem": ordem,
                },
            )
            if novo:
                nome_arquivo = f"demo-projeto-{ordem}.jpg"
                projeto.imagem.save(
                    nome_arquivo, self._imagem(nome_arquivo, 1200, 800, ordem)
                )
                projeto.tecnologias.set(tecnologias[: 2 + ordem])

    @staticmethod
    def _habilidades() -> None:
        """Cria as categorias de habilidade e as habilidades com o progresso."""
        for nome, (icone, habilidades) in HABILIDADES.items():
            categoria, _ = CategoriaHabilidade.objects.get_or_create(
                nome=nome, defaults={"icone": icone}
            )
            for habilidade, progresso in habilidades:
                Habilidade.objects.get_or_create(
                    categoria=categoria,
                    nome=habilidade,
                    defaults={"progresso": progresso},
                )

    @staticmethod
    def _estatisticas() -> None:
        """Cria as estatísticas da Home (uma delas em destaque na foto do Sobre)."""
        for ordem, (titulo, legenda, destaque) in enumerate(ESTATISTICAS):
            Estatistica.objects.get_or_create(
                titulo=titulo,
                defaults={
                    "legenda": legenda,
                    "ordem": ordem,
                    "destaque_sobre": destaque,
                },
            )
