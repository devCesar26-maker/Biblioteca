from django import forms
from .models import Autor, Categoria, Editora, Livro, LivroAutor, Emprestimo, Aluno

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
        fields=['nome', 'editora', 'categoria', 'autores', 'arquivo_pdf']
        labels = {
            'nome': 'Nome do Livro',
            'editora': 'Editora',
            'categoria': 'Categoria',
            'autores': 'Autor(es)', 
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


class EmprestimoForm(forms.ModelForm):
    class Meta:
        model=Emprestimo
        fields=['data_devolucao', 'valor', 'devolvido']
        labels={
            'data_devolucao':'Data de Devolucão',
            'valor':'Valor',
            'devolvido':'Preencha se devolveu'
        }
        data_devolucao = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-control', 'placeholder': 'dd/mm/aaaa'})
        )

class AlunoForm(forms.ModelForm):
    class Meta:
        model=Aluno
        fields=['nome']
        labels={'nome':'Digite seu nome: '}


