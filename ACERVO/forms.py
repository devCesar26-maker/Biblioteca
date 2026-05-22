from django import forms
from .models import Autor, Categoria, Editora, Livro, LivroAutor, Emprestimo, Aluno
from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
    # O campo de texto que aparecerá na mesma tela
    nome = forms.CharField(
        max_length=50, 
        label="Nome do Aluno", 
        widget=forms.TextInput(attrs={'placeholder': 'Digite seu nome completo'})
    )

    def save(self, request):
        # 1. Salva o User padrão do Allauth primeiro (gerando o username automático)
        user = super(CustomSignupForm, self).save(request)
        
        # 2. Pega o nome que o aluno digitou
        nome_digitado = self.cleaned_data['nome']
        
        # 3. Cria o registro na sua tabela Aluno vinculando ao User
        Aluno.objects.create(user=user, nome=nome_digitado)
        
        return user

class AutorForm(forms.ModelForm):
    class Meta:
        model=Autor
        fields=['nome']
        labels={'nome': 'Nome do Autor(a)'}

class CategoriaForm(forms.ModelForm):
    class Meta:
        model=Categoria
        fields=['nome']
        labels={'nome':'Nome da Categoria'}

class EditoraForm(forms.ModelForm):
    class Meta:
        model=Editora
        fields=['nome']
        labels={'nome':'Nome da Editora'}

class LivroForm(forms.ModelForm):
    class Meta:
        model=Livro
        fields=['nome', 'editora', 'categoria', 'autores', 'capa', 'valor', 'arquivo_pdf']
        labels = {
            'nome': 'Nome do Livro',
            'editora': 'Editora',
            'categoria': 'Categoria',
            'autores': 'Autor(es)', 
            'valor':'Valor',
            'capa':'Adicionar capa', 
            'arquivo_pdf': 'Adicionar PDF'
        }

class LivroAutorForm(forms.ModelForm):
    class Meta:
        model=LivroAutor
        fields=['livro', 'autor']
        labels={
            'livro':'Nome do Livro', 
            'autor':'Autor(es)'
        }



