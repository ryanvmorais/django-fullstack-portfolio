"""
👑 PROJETO: INTERFACE ADMINISTRATIVA (ADMIN.PY)
🎯 Objetivo: Educacional - Personalizar o painel de controle do Django.

ESTRUTURA DO CÓDIGO:
1. CONFIGURAÇÕES DE INTERFACE (UI): Personalização de como os dados aparecem.
2. RELACIONAMENTOS (INLINES): Gestão de modelos dependentes na mesma tela.
3. SEGURANÇA E LEITURA: Campos somente leitura e filtros de busca.
4. AUTOMAÇÃO: Preenchimento automático de campos (Slugs).
"""

from django.contrib import admin
from .models import (
    Projeto,
    CategoriaProjeto, 
    Perfil, 
    MensagemContato, 
    Tecnologia,
    CategoriaHabilidade,
    Habilidade,
    Estatistica,
)

# --- 1. CONFIGURAÇÕES DE ELEMENTOS VISUAIS ---

@admin.register(Tecnologia)
class TecnologiaAdmin(admin.ModelAdmin):
    """ Gerencia os ícones e tecnologias que aparecem no portfólio. """
    list_display = ('nome', 'ordem', 'mostrar_no_home')
    list_editable = ('ordem', 'mostrar_no_home') # Permite editar sem abrir o item
    list_filter = ('mostrar_no_home',)
    search_fields = ('nome',)

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    """ Configura a vitrine de projetos com filtros por tecnologia. """
    list_display = ('titulo', 'categoria_projeto', 'ordem') 
    list_editable = ('ordem',)
    list_filter = ('categoria_projeto', 'tecnologias')
    search_fields = ('titulo', 'descricao')
    
    # Organiza o formulário em blocos visuais (Fieldsets)
    fieldsets = (
        ('Informações do Projeto', {'fields': ('titulo', 'descricao', 'categoria_projeto', 'imagem', 'ordem')}),
        ('Tecnologias Utilizadas', {'fields': ('tecnologias',)}),
        ('Links e Repositórios', {'fields': ('link_github',)}),
    )
    
    # Interface amigável para selecionar múltiplas tecnologias (Many-to-Many)
    filter_horizontal = ('tecnologias', )

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    """ Centraliza as informações do dono do portfólio. """
    list_display = ('nome', 'cargo', 'status_trabalho')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'cargo', 'bio_curta', 'foto', 'curriculo')
        }),
        ('Sobre Mim', {
            'fields': ('bio', 'anos_experiencia', 'mostrar_progresso')
        }),
        ('Detalhes de Contato e Formação', {
            'fields': ('email_contato', 'telefone', 'localizacao', 'status_trabalho', 'formacao', 'link_linkedin', 'link_github')
        }),
    )

# --- 2. SEGURANÇA E MONITORAMENTO ---

@admin.register(MensagemContato)
class MensagemContatoAdmin(admin.ModelAdmin):
    """ 
    Gerencia os contatos recebidos. 
    Nota: Campos sensíveis são marcados como 'readonly' para evitar alteração.
    """
    list_display = ('nome', 'email', 'assunto', 'data_envio')
    list_display_links = ('nome', 'email')
    
    ordering = ('-data_envio',) # Mostra as mensagens mais recentes primeiro
    list_filter = ('data_envio',)
    
    # Segurança: Impede que alguém altere uma mensagem recebida pelo admin
    readonly_fields = ('nome', 'email', 'assunto', 'mensagem', 'data_envio')
    search_fields = ('nome', 'email', 'assunto', 'mensagem')

# --- 3. RELACIONAMENTOS E AUTOMATIZAÇÃO ---

class HabilidadeInline(admin.TabularInline):
    """ Permite adicionar habilidades diretamente dentro da categoria. """
    model = Habilidade
    extra = 1 # Define quantos campos vazios aparecem por padrão

@admin.register(CategoriaHabilidade)
class CategoriaHabilidadeAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    inlines = [HabilidadeInline] # Ativa a edição em massa de habilidades

@admin.register(Estatistica)
class EstatisticaAdmin(admin.ModelAdmin):
    list_display = ('legenda', 'titulo', 'ordem')
    list_editable = ('titulo', 'ordem')

@admin.register(CategoriaProjeto)
class CategoriaProjetoAdmin(admin.ModelAdmin):
    """ Automação de SEO: Gera o Slug automaticamente baseado no Nome. """
    list_display = ('nome', 'slug')
    prepopulated_fields = {'slug': ('nome',)}