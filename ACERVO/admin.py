from django.contrib import admin
from .models import Aluno, Autor, Categoria, Editora, Emprestimo, Livro, LivroAutor

admin.site.register(Aluno)
admin.site.register(Autor)
admin.site.register(Categoria)
admin.site.register(Editora)
admin.site.register(Emprestimo)
admin.site.register(Livro)
admin.site.register(LivroAutor)