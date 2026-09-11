"""
🗄️ PROJETO: MODELAGEM DE DADOS (MODELS.PY)
🎯 Objetivo: Educacional - Definir a estrutura do banco de dados e relacionamentos.

ESTRUTURA DO CÓDIGO:
1. ELEMENTOS AUXILIARES: Tecnologias e Categorias (Tags e Filtros).
2. NÚCLEO DO PORTFÓLIO: Projetos e Habilidades (O conteúdo principal).
3. IDENTIDADE: Perfil do Desenvolvedor e Estatísticas.
4. INTERAÇÃO: Mensagens recebidas pelo formulário.
"""

from typing import Any

from django.core.validators import MaxLengthValidator
from django.db import models

from .utils import converter_para_webp

# --- 1. ELEMENTOS AUXILIARES (TAGS E CATEGORIAS) ---


class Tecnologia(models.Model):
    """
    Representa as ferramentas (Python, Django, etc).
    Usada para exibir ícones e filtrar projetos.
    """

    nome = models.CharField(max_length=50)
    icone = models.CharField(max_length=100, help_text="Ex: python.svg", blank=True)
    mostrar_no_home = models.BooleanField(default=False)
    ordem = models.PositiveIntegerField(
        default=0, help_text="Quanto menor o número, primeiro ele aparece"
    )

    class Meta:
        ordering = ["ordem", "nome"]
        verbose_name = "Tecnologia"
        verbose_name_plural = "Tecnologias"

    def __str__(self) -> str:
        """Returns: str: O nome da tecnologia."""
        return self.nome


class CategoriaProjeto(models.Model):
    """Define os tipos de projeto (Web, Mobile, Data Science)."""

    nome = models.CharField(max_length=50)
    # O Slug é uma versão amigável da URL (ex: 'web-development')
    slug = models.SlugField(
        unique=True, help_text="Nome usado no filtro (ex: web, api, mobile)"
    )

    class Meta:
        verbose_name = "Categoria de Projeto"
        verbose_name_plural = "Categorias de Projetos"

    def __str__(self) -> str:
        """Returns: str: O nome da categoria."""
        return self.nome


# --- 2. NÚCLEO DO PORTFÓLIO (CONTEÚDO) ---


class Projeto(models.Model):
    """
    O modelo principal que une Categoria, Texto e Tecnologias.
    Demonstra relacionamentos ForeignKey, ManyToMany e processamento de imagem com Pillow.
    """

    # ForeignKey: Um projeto tem UMA categoria (Um-para-Muitos)
    categoria_projeto = models.ForeignKey(
        CategoriaProjeto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projetos",
    )
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(
        help_text="Mantenha por volta de 170 caracteres para simetria"
    )
    imagem = models.ImageField(
        upload_to="projetos/",
        null=True,
        blank=True,
        help_text="Upload em JPG ou PNG. O sistema converterá para WebP automaticamente para performance.",
    )

    # ManyToMany: Um projeto usa várias tecnologias, e uma tecnologia está em vários projetos.
    tecnologias = models.ManyToManyField(Tecnologia)

    link_github = models.URLField(blank=True, null=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        ordering = ["ordem"]
        verbose_name = "Projeto"
        verbose_name_plural = "Projetos"

    def __str__(self) -> str:
        """Returns: str: O título do projeto."""
        return self.titulo

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Sobrescrita do save utilizando a função utilitária global.

        Mantém o DRY (Don't Repeat Yourself) e a performance.

        Args:
            *args (Any): Argumentos posicionais repassados ao ``super().save()``.
            **kwargs (Any): Argumentos nomeados repassados ao ``super().save()``.
        """
        # Chamada da função modularizada em utils.py
        novo_conteudo, novo_nome = converter_para_webp(self.imagem)

        if novo_conteudo and novo_nome:
            self.imagem.save(novo_nome, novo_conteudo, save=False)

        super().save(*args, **kwargs)


# --- 3. IDENTIDADE E APRESENTAÇÃO ---


class Perfil(models.Model):
    """
    Armazena todos os dados do desenvolvedor.
    Centraliza informações que mudam pouco (Nome, Bio, Links).
    """

    nome = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    foto = models.ImageField(
        upload_to="perfil/",
        null=True,
        blank=True,
        help_text="Sua foto de apresentação. Será convertida para WebP para agilizar o carregamento da Home.",
    )
    bio = models.TextField(blank=True, null=True)
    bio_curta = models.CharField(max_length=255, blank=True, null=True)
    anos_experiencia = models.IntegerField(default=0)
    mostrar_progresso = models.BooleanField(
        default=False,
        verbose_name="Exibir barras de progresso",
        help_text="Marque para exibir as porcentagens de domínio nas habilidades.",
    )
    email_contato = models.EmailField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    localizacao = models.CharField(max_length=100, blank=True, null=True)
    status_trabalho = models.CharField(max_length=100, blank=True, null=True)
    formacao = models.CharField(max_length=100, blank=True, null=True)
    curriculo = models.FileField(upload_to="curriculo/", null=True, blank=True)
    link_linkedin = models.URLField(blank=True, null=True)
    link_github = models.URLField(blank=True, null=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self) -> str:
        """Returns: str: O nome do desenvolvedor."""
        return self.nome

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Garante que a foto de perfil seja sempre leve.

        Impacta positivamente na pontuação de performance do site.

        Args:
            *args (Any): Argumentos posicionais repassados ao ``super().save()``.
            **kwargs (Any): Argumentos nomeados repassados ao ``super().save()``.
        """
        novo_conteudo, novo_nome = converter_para_webp(self.foto)

        if novo_conteudo and novo_nome:
            self.foto.save(novo_nome, novo_conteudo, save=False)

        super().save(*args, **kwargs)


class Estatistica(models.Model):
    """Dados rápidos para a Hero Section (ex: "50+ Projetos")."""

    titulo = models.CharField(max_length=10, help_text="Ex: 5+ ou 50+")
    legenda = models.TextField(
        max_length=100, help_text="Dê um 'Enter' onde deseja quebrar a linha"
    )
    ordem = models.PositiveIntegerField(
        default=0, help_text="Define a posição de exibição"
    )
    destaque_sobre = models.BooleanField(
        default=False, verbose_name="Destaque na foto Sobre Mim"
    )

    class Meta:
        verbose_name = "Estatística"
        verbose_name_plural = "Estatísticas"
        ordering = ["ordem"]

    def __str__(self) -> str:
        """Returns: str: A legenda da estatística."""
        return self.legenda


# --- 4. HABILIDADES E CATEGORIAS ---


class CategoriaHabilidade(models.Model):
    """Organiza habilidades em grupos (Backend, UI/UX, etc)."""

    nome = models.CharField(max_length=50)
    icone = models.CharField(
        max_length=50, help_text="Nome da classe ou arquivo do ícone", blank=True
    )

    class Meta:
        verbose_name = "Categoria de Habilidade"
        verbose_name_plural = "Categorias de Habilidades"

    def __str__(self) -> str:
        """Returns: str: O nome da categoria de habilidade."""
        return self.nome


class Habilidade(models.Model):
    """Habilidades individuais ligadas a uma categoria."""

    categoria = models.ForeignKey(
        CategoriaHabilidade, on_delete=models.CASCADE, related_name="habilidades"
    )
    nome = models.CharField(max_length=50)
    progresso = models.IntegerField(default=0, help_text="Nível de 0 a 100")

    def __str__(self) -> str:
        """Returns: str: Formato "nome (categoria)"."""
        return f"{self.nome} ({self.categoria.nome})"


# --- 5. INTERAÇÃO E LOGS ---


class MensagemContato(models.Model):
    """Registra as tentativas de contato feitas pelo site."""

    nome = models.CharField(max_length=100)
    email = models.EmailField()
    assunto = models.CharField(max_length=200)
    mensagem = models.TextField(validators=[MaxLengthValidator(5000)])
    data_envio = models.DateTimeField(
        auto_now_add=True
    )  # Data gerada automaticamente no envio
    lida = models.BooleanField(default=False)

    class Meta:
        ordering = ["-data_envio"]
        verbose_name = "Mensagem de Contato"
        verbose_name_plural = "Mensagens de Contato"

    def __str__(self) -> str:
        """Returns: str: Formato "nome - assunto"."""
        return f"{self.nome} - {self.assunto}"
