"""
📝 PROJETO: FORMULÁRIOS DO SISTEMA (FORMS.PY)
🎯 Objetivo: Educacional - Automatizar a criação e validação de formulários.

ESTRUTURA DO CÓDIGO:
1. MODEL FORM: Vinculação direta entre o formulário e o banco de dados.
"""

from django import forms
from .models import MensagemContato

# O ModelForm é uma classe sênior que "lê" o seu modelo e 
# cria os campos automaticamente com as validações já prontas.
class MensagemContatoForm(forms.ModelForm):
    """
    Formulário responsável por capturar mensagens na Home.
    Herda as regras de validação definidas no modelo MensagemContato.
    """
    class Meta:
        # Vinculamos este formulário ao modelo de mensagens
        model = MensagemContato
        
        # Definimos exatamente quais campos do banco aparecerão no site
        fields = ['nome', 'email', 'assunto', 'mensagem']