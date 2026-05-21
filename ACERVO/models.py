from django.db import models
from django.contrib.auth.models import User


class Aluno(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome


class Autor(models.Model):
    nome = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    nome = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return self.nome


class Editora(models.Model):
    nome = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return self.nome


class Livro(models.Model):
    nome = models.CharField(unique=True, max_length=70)
    editora = models.ForeignKey(Editora, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    autores = models.ManyToManyField(Autor, through='LivroAutor')
    arquivo_pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)


    def __str__(self):
        return self.nome


class Emprestimo(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    data_emprestimo = models.DateField()
    data_devolucao = models.DateField()
    valor = models.FloatField(blank=True, null=True)
    devolvido = models.BooleanField(default=False)
    livro= models.ForeignKey(Livro, on_delete=models.CASCADE)

    renovacoes = models.PositiveIntegerField(default=0)
    
    MAXIMO_RENOVACOES=3

    def __str__(self):
        return f"Empréstimo {self.id} - {self.aluno.nome}"


class LivroAutor(models.Model):
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('livro', 'autor')

    def __str__(self):
        return f"{self.livro} - {self.autor}"
