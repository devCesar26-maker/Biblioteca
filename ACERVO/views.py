from django.shortcuts import render, redirect, get_object_or_404
from .models import Autor, Categoria, Editora, Livro, Aluno, Emprestimo
from .forms import AutorForm, CategoriaForm, EditoraForm, LivroForm, LivroAutorForm, EmprestimoForm, AlunoForm
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from datetime import date
from functools import wraps
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Count


# Decorador para barrar acesso de não-superusuários
def superuser_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise Http404("Página não encontrada")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# Decorador para barrar leitura do livro caso a licença esteja expirada
def licenca_valida(view_func):
    @wraps(view_func)
    def _wrapped_view(request, livro_id, *args, **kwargs):
        aluno = get_object_or_404(Aluno, user=request.user)
        emprestimos = Emprestimo.objects.filter(livro_id=livro_id, aluno=aluno)
        emprestimo = emprestimos.order_by('-data_devolucao').first()

        if emprestimo.devolvido or timezone.now().date() > emprestimo.data_devolucao:
            return redirect('licenca_expirada')
        return view_func(request, livro_id, *args, **kwargs)
    return _wrapped_view


# Página da licença expirada
def licenca_expirada(request):
    return render(request, "ACERVO/licenca_expirada.html")


# Página principal
def index(request):
    return render(request, 'ACERVO/index.html')


# --- Alunos ---
@login_required
def criar_aluno(request):
    if request.method != 'POST':
        form = AlunoForm()
    else:
        nome = request.POST.get("nome")
        request.user.first_name = nome
        request.user.save()
        form = AlunoForm(request.POST)
        if form.is_valid():
            aluno = form.save(commit=False)
            aluno.user = request.user
            aluno.save()
            return HttpResponseRedirect(reverse('index'))
    context = {'form': form}
    return render(request, "ACERVO/criar_aluno.html", context)


# --- Autores ---
@login_required
def autores(request):
    autores = Autor.objects.all()
    context = {'autores': autores}
    return render(request, "ACERVO/autores.html", context)

@login_required
@permission_required('ACERVO.add_autor', raise_exception=True)
def new_autor(request):
    if request.method != 'POST':
        form = AutorForm()
    else:
        form = AutorForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('autores'))
    context = {'form': form}
    return render(request, "ACERVO/new_autor.html", context)


# --- Categorias ---
@login_required
def categorias(request):
    categorias = Categoria.objects.all()
    context = {'categorias': categorias}
    return render(request, "ACERVO/categorias.html", context)

@login_required
@permission_required('ACERVO.add_categoria', raise_exception=True)
def new_categoria(request):
    if request.method != 'POST':
        form = CategoriaForm()
    else:
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('categorias'))
    context = {'form': form}
    return render(request, "ACERVO/new_categoria.html", context)


# --- Editoras ---
@login_required
def editoras(request):
    editoras = Editora.objects.all()
    context = {'editoras': editoras}
    return render(request, "ACERVO/editoras.html", context)

@login_required
@permission_required('ACERVO.add_editora', raise_exception=True)
def new_editora(request):
    if request.method != 'POST':
        form = EditoraForm()
    else:
        form = EditoraForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('editoras'))
    context = {'form': form}
    return render(request, "ACERVO/new_editora.html", context)


# --- Livros ---
@login_required
def livros(request):
    livros = Livro.objects.all()
    context = {'livros': livros}
    return render(request, "ACERVO/livros.html", context)

@login_required
@permission_required('ACERVO.add_livro', raise_exception=True)
def new_livro(request):
    if request.method != 'POST':
        form = LivroForm()
    else:
        form = LivroForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('livros'))
    context = {'form': form}
    return render(request, "ACERVO/new_livro.html", context)

@login_required
def data_livro(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)
    autores = livro.autores.all()
    context = {'livro': livro, 'autores': autores}
    return render(request, "ACERVO/dados_livros.html", context)


# --- LivroAutor ---
@login_required
@permission_required('ACERVO.add_livroautor', raise_exception=True)
def new_livro_autor(request):
    if request.method != 'POST':
        form = LivroAutorForm()
    else:
        form = LivroAutorForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('livros'))
    context = {'form': form}
    return render(request, "ACERVO/new_livro_autor.html", context)


# --- Empréstimos ---
@login_required
def meus_emprestimos(request):
    aluno = get_object_or_404(Aluno, user=request.user)
    emprestimos = Emprestimo.objects.filter(aluno=aluno)
    for e in emprestimos:
        dias_restantes = (e.data_devolucao - timezone.now().date()).days
        if 0< dias_restantes <= 2 and not e.devolvido:
            messages.warning(request, f"⚠️ O empréstimo do livro '{e.livro.nome}' vence em {dias_restantes} dias!")
        if dias_restantes<=0:
            excesso=(timezone.now().date()-e.data_devolucao).days
            messages.warning(request, f"⚠️ O empréstimo do livro '{e.livro.nome}' venceu há {excesso} dias!")
    context = {'emprestimos': emprestimos}
    return render(request, "ACERVO/meus_emprestimos.html", context)

@login_required
def fazer_emprestimo(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)
    aluno = get_object_or_404(Aluno, user=request.user)
    if request.method != 'POST':
        form = EmprestimoForm()
    else:
        form = EmprestimoForm(request.POST)
        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.aluno = aluno
            emprestimo.livro = livro
            emprestimo.data_emprestimo = date.today()
            emprestimo.save()

            messages.success(request, f"Emprestimo do '{livro.nome}' realizado com sucesso!")
            return HttpResponseRedirect(reverse('meus_emprestimos'))
    context = {'form': form, 'livro': livro}
    return render(request, 'ACERVO/new_emprestimo.html', context)


@login_required
def renovar_emprestimo(request, livro_id):
    aluno = get_object_or_404(Aluno, user=request.user)
    livro = get_object_or_404(Livro, id=livro_id)

    emprestimo = Emprestimo.objects.filter(aluno=aluno, livro=livro).order_by('-data_devolucao').first()

    if emprestimo and not emprestimo.devolvido:
        if emprestimo.renovacoes < Emprestimo.MAXIMO_RENOVACOES:
            emprestimo.data_devolucao += timedelta(days=7)
            emprestimo.valor = (emprestimo.valor or 0) + 10  # evita erro se valor for None
            emprestimo.renovacoes += 1
            emprestimo.save()
            messages.success(
                request,
                f"O empréstimo do livro '{livro.nome}' foi renovado por mais 7 dias! "
                f"(Renovações: {emprestimo.renovacoes}/{Emprestimo.MAXIMO_RENOVACOES})"
            )
        else:
            messages.error(
                request,
                "❌ Você já atingiu o limite máximo de renovações. "
                "Caso queira ler novamente, faça um novo empréstimo."
            )
    else:
        messages.error(request, "Não foi possível renovar este empréstimo.")

    return redirect('meus_emprestimos')

# --- Visualizar PDF ---
@login_required
@licenca_valida
def visualizar_pdf(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)
    aluno = Aluno.objects.get(user=request.user)
    emprestimo = get_object_or_404(Emprestimo, aluno=aluno, livro=livro)
    return render(request, "ACERVO/visualizar_pdf.html", {'livro': livro, 'emprestimo': emprestimo})


@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    resultados = Livro.objects.none()

    if query:
        search_vector = (
            SearchVector('nome', weight='A') +
            SearchVector('editora__nome', weight='B') +
            SearchVector('categoria__nome', weight='B') +
            SearchVector('autores__nome', weight='A')
        )

        search_query = SearchQuery(query, search_type='websearch')

        resultados = Livro.objects.annotate(
            rank=SearchRank(search_vector, search_query)
        ).filter(rank__gte=0.1).order_by('-rank').distinct()

    return render(request, "ACERVO/search_results.html", {
        'query': query,
        'resultados': resultados
    })

@login_required
def dashboard(request):
    # Estatísticas simples
    total_livros = Livro.objects.count()
    total_emprestimos = Emprestimo.objects.count()
    emprestimos_por_categoria = (
        Emprestimo.objects.values('livro__categoria__nome')
        .annotate(total=Count('id'))
    )

    context = {
        'total_livros': total_livros,
        'total_emprestimos': total_emprestimos,
        'emprestimos_por_categoria': emprestimos_por_categoria,
    }
    return render(request, 'ACERVO/dashboard.html', context)


#Edição de Autores
@login_required
@permission_required('ACERVO.change_autor', raise_exception=True)
def edit_autor(request, autor_id):
    autor=get_object_or_404(Autor, id=autor_id)
   

    if request.method!='POST':
        form=AutorForm(instance=autor)

    else:
        form=AutorForm(instance=autor, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('autores'))
        
    context={'autor':autor, 'form':form}
    return render(request, "ACERVO/edit_autor.html", context)


@login_required
@permission_required('ACERVO.change_categoria', raise_exception=True)
def edit_categoria(request, categoria_id):
    categoria=get_object_or_404(Categoria, id=categoria_id)

    if request.method!='POST':
        form=CategoriaForm(instance=categoria)

    else:
        form=CategoriaForm(instance=categoria, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('categorias'))
        
    context={'categoria':categoria, 'form':form}
    return render(request, "ACERVO/edit_categoria.html", context)


@login_required
@permission_required('ACERVO.change_editora', raise_exception=True)
def edit_editora(request, editora_id):
    editora=get_object_or_404(Editora, id=editora_id)

    if request.method!='POST':
        form=EditoraForm(instance=editora)

    else:
        form=EditoraForm(instance=editora, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('editoras'))
        
    context={'editora':editora, 'form':form}
    return render(request, "ACERVO/edit_editora.html", context)
 
#Deletar autores
@login_required
@permission_required('ACERVO.delete_livroautor', raise_exception=True)
def deletar_autor(request, autor_id):
    autor=get_object_or_404(Autor, id=autor_id)
    autor.delete()
    return redirect('autores')


