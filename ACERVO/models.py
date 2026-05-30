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
    capa = models.CharField(max_length=70, blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    arquivo_pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)

    def __str__(self):
        return self.nome


class Emprestimo(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    data_emprestimo = models.DateField()
    data_devolucao = models.DateField()
    data_ultima_renovacao = models.DateField(null=True, blank=True)
    
    # Alterado para DecimalField para combinar perfeitamente com o valor do Livro
    valor = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    devolvido = models.BooleanField(default=False)
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE)
    renovacoes = models.PositiveIntegerField(default=0)
    
    MAXIMO_RENOVACOES = 3

    def save(self, *args, **kwargs):
        # Se for um empréstimo novo (ainda não tem ID no banco) e um livro foi selecionado
        if not self.id and self.livro:
            # Ele busca o valor direto do livro selecionado e salva aqui
            self.valor = self.livro.valor
            
        # Executa o salvamento normal do Django
        super(Emprestimo, self).save(*args, **kwargs)

    def __str__(self):
        return f"Empréstimo {self.id} - {self.aluno.nome}"
    

class LivroAutor(models.Model):
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE)
    autor = models.ForeignKey(Autor, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('livro', 'autor')

    def __str__(self):
        return f"{self.livro} - {self.autor}"
