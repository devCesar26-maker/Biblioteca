import unittest
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Aluno, Categoria, Editora, Emprestimo, Livro


def criar_livro(nome='Livro Teste', valor=Decimal('19.90'), arquivo_pdf=None):
    editora, _ = Editora.objects.get_or_create(nome='Editora Teste')
    categoria, _ = Categoria.objects.get_or_create(nome='Categoria Teste')
    return Livro.objects.create(
        nome=nome, editora=editora, categoria=categoria, valor=valor,
        arquivo_pdf=arquivo_pdf,
    )


class EmprestimoModelTests(TestCase):
    def test_save_copia_valor_do_livro(self):
        livro = criar_livro(valor=Decimal('42.50'))
        aluno = Aluno.objects.create(nome='Aluno Teste')

        emprestimo = Emprestimo.objects.create(
            aluno=aluno,
            livro=livro,
            data_emprestimo=timezone.localdate(),
            data_devolucao=timezone.localdate() + timedelta(days=7),
        )

        self.assertEqual(emprestimo.valor, Decimal('42.50'))


class IndexViewTests(TestCase):
    def test_index_retorna_200(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)


class LivrosViewTests(TestCase):
    def test_livros_exige_login(self):
        response = self.client.get(reverse('livros'))
        self.assertRedirects(response, f"{reverse('account_login')}?next={reverse('livros')}")

    def test_livros_lista_acervo(self):
        user = User.objects.create_user(username='leitor', password='senha123')
        self.client.force_login(user)
        criar_livro(nome='Livro A')

        response = self.client.get(reverse('livros'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Livro A')


class EmprestimoViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='aluno', email='aluno@teste.com', password='senha123'
        )
        self.aluno = Aluno.objects.create(user=self.user, nome='Aluno Teste')
        self.livro = criar_livro()
        self.client.force_login(self.user)

    def test_fazer_emprestimo_cria_registro(self):
        response = self.client.post(reverse('fazer_emprestimo', args=[self.livro.id]))

        self.assertRedirects(response, reverse('meus_emprestimos'))
        emprestimo = Emprestimo.objects.get(aluno=self.aluno, livro=self.livro)
        self.assertFalse(emprestimo.devolvido)
        self.assertEqual(emprestimo.valor, self.livro.valor)
        self.assertEqual(
            emprestimo.data_devolucao - emprestimo.data_emprestimo,
            timedelta(days=7),
        )

    def test_fazer_emprestimo_nao_duplica_emprestimo_ativo(self):
        self.client.post(reverse('fazer_emprestimo', args=[self.livro.id]))
        response = self.client.post(reverse('fazer_emprestimo', args=[self.livro.id]))

        self.assertRedirects(response, reverse('meus_emprestimos'))
        self.assertEqual(Emprestimo.objects.filter(livro=self.livro).count(), 1)

    def test_fazer_emprestimo_exige_cadastro_de_aluno(self):
        usuario_sem_aluno = User.objects.create_user(
            username='semaluno', password='senha123'
        )
        self.client.force_login(usuario_sem_aluno)

        response = self.client.post(reverse('fazer_emprestimo', args=[self.livro.id]))

        self.assertRedirects(response, reverse('livros'))
        self.assertEqual(Emprestimo.objects.count(), 0)

    def test_renovar_emprestimo_adiciona_7_dias_e_valor(self):
        emprestimo = Emprestimo.objects.create(
            aluno=self.aluno,
            livro=self.livro,
            data_emprestimo=timezone.localdate() - timedelta(days=10),
            data_devolucao=timezone.localdate() + timedelta(days=1),
            data_ultima_renovacao=timezone.localdate() - timedelta(days=6),
        )

        response = self.client.post(reverse('renovar_emprestimo', args=[self.livro.id]))

        self.assertRedirects(response, reverse('meus_emprestimos'))
        emprestimo.refresh_from_db()
        self.assertEqual(emprestimo.renovacoes, 1)
        self.assertEqual(emprestimo.valor, self.livro.valor * 2)
        self.assertEqual(emprestimo.data_ultima_renovacao, timezone.localdate())
        self.assertEqual(emprestimo.data_devolucao, timezone.localdate() + timedelta(days=8))

    def test_renovar_emprestimo_bloqueia_atrasado(self):
        emprestimo = Emprestimo.objects.create(
            aluno=self.aluno,
            livro=self.livro,
            data_emprestimo=timezone.localdate() - timedelta(days=10),
            data_devolucao=timezone.localdate() - timedelta(days=1),
        )

        self.client.post(reverse('renovar_emprestimo', args=[self.livro.id]))

        emprestimo.refresh_from_db()
        self.assertEqual(emprestimo.renovacoes, 0)

    def test_renovar_emprestimo_bloqueia_intervalo_menor_que_5_dias(self):
        emprestimo = Emprestimo.objects.create(
            aluno=self.aluno,
            livro=self.livro,
            data_emprestimo=timezone.localdate() - timedelta(days=3),
            data_devolucao=timezone.localdate() + timedelta(days=4),
        )

        self.client.post(reverse('renovar_emprestimo', args=[self.livro.id]))

        emprestimo.refresh_from_db()
        self.assertEqual(emprestimo.renovacoes, 0)
        self.assertEqual(emprestimo.data_devolucao, timezone.localdate() + timedelta(days=4))

    def test_renovar_emprestimo_bloqueia_limite_de_renovacoes(self):
        emprestimo = Emprestimo.objects.create(
            aluno=self.aluno,
            livro=self.livro,
            data_emprestimo=timezone.localdate() - timedelta(days=30),
            data_devolucao=timezone.localdate() + timedelta(days=1),
            data_ultima_renovacao=timezone.localdate() - timedelta(days=6),
            renovacoes=Emprestimo.MAXIMO_RENOVACOES,
        )

        self.client.post(reverse('renovar_emprestimo', args=[self.livro.id]))

        emprestimo.refresh_from_db()
        self.assertEqual(emprestimo.renovacoes, Emprestimo.MAXIMO_RENOVACOES)


class VisualizarPdfViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='leitor', password='senha123')
        self.livro = criar_livro()
        self.client.force_login(self.user)

    def test_sem_cadastro_de_aluno_retorna_404(self):
        response = self.client.get(reverse('visualizar_pdf', args=[self.livro.id]))
        self.assertEqual(response.status_code, 404)

    def test_sem_emprestimo_ativo_redireciona_para_licenca_expirada(self):
        Aluno.objects.create(user=self.user, nome='Leitor Teste')

        response = self.client.get(reverse('visualizar_pdf', args=[self.livro.id]))

        self.assertRedirects(response, reverse('licenca_expirada'))

    def test_com_emprestimo_ativo_retorna_200(self):
        livro_com_pdf = criar_livro(nome='Livro Com PDF', arquivo_pdf='pdfs/exemplo.pdf')
        aluno = Aluno.objects.create(user=self.user, nome='Leitor Teste')
        Emprestimo.objects.create(
            aluno=aluno,
            livro=livro_com_pdf,
            data_emprestimo=timezone.localdate(),
            data_devolucao=timezone.localdate() + timedelta(days=7),
        )

        response = self.client.get(reverse('visualizar_pdf', args=[livro_com_pdf.id]))

        self.assertEqual(response.status_code, 200)

    def test_livro_sem_pdf_redireciona_com_erro(self):
        aluno = Aluno.objects.create(user=self.user, nome='Leitor Teste')
        Emprestimo.objects.create(
            aluno=aluno,
            livro=self.livro,
            data_emprestimo=timezone.localdate(),
            data_devolucao=timezone.localdate() + timedelta(days=7),
        )

        response = self.client.get(reverse('visualizar_pdf', args=[self.livro.id]))

        self.assertRedirects(response, reverse('meus_emprestimos'))


class DadosLivrosPdfGatingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='leitor', password='senha123')
        self.aluno = Aluno.objects.create(user=self.user, nome='Leitor Teste')
        self.livro = criar_livro(arquivo_pdf='pdfs/exemplo.pdf')
        self.client.force_login(self.user)

    def test_sem_emprestimo_ativo_nao_libera_pdf(self):
        response = self.client.get(reverse('dados_livros', args=[self.livro.id]))
        self.assertFalse(response.context['pode_ler_pdf'])

    def test_com_emprestimo_ativo_dentro_do_prazo_libera_pdf(self):
        Emprestimo.objects.create(
            aluno=self.aluno,
            livro=self.livro,
            data_emprestimo=timezone.localdate(),
            data_devolucao=timezone.localdate() + timedelta(days=7),
        )

        response = self.client.get(reverse('dados_livros', args=[self.livro.id]))

        self.assertTrue(response.context['pode_ler_pdf'])
        self.assertContains(response, reverse('visualizar_pdf', args=[self.livro.id]))

    def test_emprestimo_vencido_nao_libera_pdf(self):
        Emprestimo.objects.create(
            aluno=self.aluno,
            livro=self.livro,
            data_emprestimo=timezone.localdate() - timedelta(days=10),
            data_devolucao=timezone.localdate() - timedelta(days=1),
        )

        response = self.client.get(reverse('dados_livros', args=[self.livro.id]))

        self.assertFalse(response.context['pode_ler_pdf'])


@unittest.skipUnless(connection.vendor == 'postgresql', 'Busca textual requer PostgreSQL')
class SearchViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='leitor', password='senha123')
        self.client.force_login(self.user)

    def test_busca_retorna_livro_correspondente(self):
        criar_livro(nome='Python para Iniciantes')

        response = self.client.get(reverse('search'), {'q': 'Python'})

        self.assertContains(response, 'Python para Iniciantes')
        self.assertNotContains(response, 'Nenhuma obra encontrada')

    def test_busca_sem_resultado(self):
        response = self.client.get(reverse('search'), {'q': 'inexistente'})
        self.assertContains(response, 'Nenhuma obra encontrada')
