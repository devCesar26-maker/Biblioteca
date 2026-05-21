from .import views
from django.urls import path
urlpatterns = [
    path('', views.index, name='index'), 
    path('autores', views.autores, name='autores'), 
    path('new_autor', views.new_autor, name='new_autor'),
    path('categorias', views.categorias, name='categorias'), 
    path('new_categoria', views.new_categoria, name='new_categoria'), 
    path('editoras', views.editoras, name='editoras'), 
    path('new_editora', views.new_editora, name='new_editora'), 
    path('livros', views.livros, name='livros'), 
    path('new_livro', views.new_livro, name='new_livro'), 
    path('livros/<livro_id>', views.data_livro, name='dados_livros'), 
    path('new_livro_autor', views.new_livro_autor, name='new_livro_autor'), 
    path('meus_emprestimos', views.meus_emprestimos, name='meus_emprestimos'), 
    path('livros/new_emprestimo/<int:livro_id>', views.fazer_emprestimo, name='fazer_emprestimo'), 
    path('meus_emprestimos/<livro_id>', views.visualizar_pdf, name='visualizar_pdf'), 
    path('licenca_expirada', views.licenca_expirada, name='licenca_expirada'), 
    path('livros/renovar/<livro_id>', views.renovar_emprestimo, name='renovar_emprestimo'), 
    path('buscar', views.search, name='search'), 
    path('dashboard/', views.dashboard, name='dashboard'),
    path('autores/edit_autor/<autor_id>', views.edit_autor, name='edit_autor'), 
    path('categorias/edit_categoria/<categoria_id>', views.edit_categoria, name='edit_categoria'), 
    path('editoras/edit_editora/<editora_id>', views.edit_editora, name='edit_editora'), 
]















