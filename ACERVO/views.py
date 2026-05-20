from django.shortcuts import render, redirect, get_object_or_404
from .models import Autor, Categoria, Editora, Livro, Aluno, Emprestimo
from .forms import AutorForm, CategoriaForm, EditoraForm, LivroForm, LivroAutorForm, EmprestimoForm, AlunoForm
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from datetime import date, timedelta
from functools import wraps
from django.utils import timezone
from django.contrib import messages
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Count


# Decorador para barrar acesso de não-superusuários
def superuser_required(view_func):
    @wraps(view_func)
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
        emprestimo = Emprestimo.objects.filter(livro_id=livro_id, aluno=aluno).order_by('-data_devolucao').first()

        # Evita quebrar se o aluno nunca tiver pego o livro emprestado
        if not emprestimo or emprestimo.devolvido or timezone.localdate() > emprestimo.data_devolucao:
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
    if request.method == 'POST':
        form = AlunoForm(request.POST)
        if form.is_valid():
            # BOA PRÁTICA: Pegar o nome já limpo e validado pelo formulário
            nome = form.cleaned_data.get("nome")
            
            # Atualiza o primeiro nome no usuário do Django
            request.user.first_name = nome
            request.user.save()
            
            # Associa o Aluno ao Usuário e salva no banco
            aluno = form.save(commit=False)
            aluno.user = request.user
            aluno.save()
            
            messages.success(request, f"Perfil criado com sucesso, bem-vindo(a) {nome}!")
            return HttpResponseRedirect(reverse('index'))
    else:
        form = AlunoForm()
        
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
        # Corrigido: Incluído request.FILES para suportar o recebimento de mídias/PDFs
        form = LivroForm(request.POST, request.FILES)
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
    # Proteção para o fluxo Allauth: se o usuário logado não tiver Aluno criado, manda criar
    aluno = Aluno.objects.filter(user=request.user).first()
    if not aluno:
        messages.warning(request, "Por favor, crie seu perfil de aluno primeiro.")
        return redirect('criar_aluno')
        
    emprestimos = Emprestimo.objects.filter(aluno=aluno)
    hoje = timezone.localdate()
    
    # Criamos variáveis dinâmicas no Python para você usar no HTML,
    # evitando que a tela fique cheia de alertas repetidos a cada "F5"
    for e in emprestimos:
        if not e.devolvido:
            e.dias_restantes = (e.data_devolucao - hoje).days
            e.atrasado = e.dias_restantes < 0
            if e.atrasado:
                e.dias_excesso = abs(e.dias_restantes)
                
    context = {'emprestimos': emprestimos, 'hoje': hoje}
    return render(request, "ACERVO/meus_emprestimos.html", context)


@login_required
def fazer_emprestimo(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)
    
    # Proteção: Verifica com .first() se o usuário já criou o perfil de Aluno
    aluno = Aluno.objects.filter(user=request.user).first()
    if not aluno:
        messages.error(request, "Você precisa preencher seu nome completo primeiro!")
        return redirect('criar_aluno')

    # 1. Checa se o aluno já tem ESSE livro em aberto (independente de data de vencimento)
    emprestimo_ativo = Emprestimo.objects.filter(
        aluno=aluno,
        livro=livro,
        devolvido=False
    ).exists()
    
    if emprestimo_ativo:
        messages.error(request, "Você já tem um empréstimo ativo com esse livro.")
        return redirect('meus_emprestimos')

    # 2. Processa o formulário de empréstimo
    if request.method == 'POST':
        form = EmprestimoForm(request.POST)
        if form.is_valid():
            emprestimo = form.save(commit=False)
            emprestimo.aluno = aluno
            emprestimo.livro = livro
            
            # --- CÁLCULO AUTOMÁTICO DAS DATAS ---
            hoje = timezone.localdate()
            emprestimo.data_emprestimo = hoje
            emprestimo.data_devolucao = hoje + timedelta(days=7) # Prazo automático de 7 dias
            emprestimo.devolvido = False
            # ------------------------------------
            
            emprestimo.save()

            messages.success(request, f"Empréstimo do '{livro.nome}' realizado com sucesso!")
            return redirect('meus_emprestimos')
    else:
        form = EmprestimoForm()
            
    context = {'form': form, 'livro': livro}
    return render(request, 'ACERVO/new_emprestimo.html', context)


@login_required
def renovar_emprestimo(request, livro_id):
    aluno = Aluno.objects.filter(user=request.user).first()
    if not aluno:
        return redirect('criar_aluno')
        
    livro = get_object_or_404(Livro, id=livro_id)

    # CORREÇÃO: Busca estritamente o empréstimo que NÃO foi devolvido ainda
    emprestimo = Emprestimo.objects.filter(aluno=aluno, livro=livro, devolvido=False).first()

    if emprestimo:
        if emprestimo.renovacoes < Emprestimo.MAXIMO_RENOVACOES:
            emprestimo.data_devolucao += timedelta(days=7)
            emprestimo.valor = (emprestimo.valor or 0) + 10
            emprestimo.renovacoes += 1
            emprestimo.save()
            messages.success(
                request,
                f"O empréstimo do livro '{livro.nome}' foi renovado por mais 7 dias! "
                f"({emprestimo.renovacoes}/{Emprestimo.MAXIMO_RENOVACOES})"
            )
        else:
            messages.error(
                request,
                f"❌ Você já atingiu o limite máximo de {Emprestimo.MAXIMO_RENOVACOES} renovações para este livro."
            )
    else:
        messages.error(request, "Você não possui um empréstimo ativo deste livro para renovar.")

    return redirect('meus_emprestimos')


@login_required
@licenca_valida
def visualizar_pdf(request, livro_id):
    aluno = Aluno.objects.filter(user=request.user).first()
    if not aluno:
        raise Http404("Perfil de aluno não encontrado.")
        
    livro = get_object_or_404(Livro, id=livro_id)
    
    # CORREÇÃO: Só permite ler o PDF se ele tiver o empréstimo ATIVO (não devolvido)
    emprestimo = Emprestimo.objects.filter(aluno=aluno, livro=livro, devolvido=False).first()
    
    if not emprestimo:
        messages.error(request, "Você precisa ter um empréstimo ativo para visualizar este livro.")
        return redirect('meus_emprestimos')
        
    return render(request, "ACERVO/visualizar_pdf.html", {'livro': livro, 'emprestimo': emprestimo})# --- Mecanismo de Busca ---
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


# --- Dashboard ---
@login_required
def dashboard(request):
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


# --- Edição de Registros ---
@login_required
@permission_required('ACERVO.change_autor', raise_exception=True)
def edit_autor(request, autor_id):
    autor = get_object_or_404(Autor, id=autor_id)

    if request.method != 'POST':
        form = AutorForm(instance=autor)
    else:
        form = AutorForm(instance=autor, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('autores'))
        
    context = {'autor': autor, 'form': form}
    return render(request, "ACERVO/edit_autor.html", context)


@login_required
@permission_required('ACERVO.change_categoria', raise_exception=True)
def edit_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id=categoria_id)

    if request.method != 'POST':
        form = CategoriaForm(instance=categoria)
    else:
        form = CategoriaForm(instance=categoria, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('categorias'))
        
    context = {'categoria': categoria, 'form': form}
    return render(request, "ACERVO/edit_categoria.html", context)


@login_required
@permission_required('ACERVO.change_editora', raise_exception=True)
def edit_editora(request, editora_id):
    editora = get_object_or_404(Editora, id=editora_id)

    if request.method != 'POST':
        form = EditoraForm(instance=editora)
    else:
        form = EditoraForm(instance=editora, data=request.POST)
        if form.is_valid():
            return HttpResponseRedirect(reverse('editoras'))
        
    context = {'editora': editora, 'form': form}
    return render(request, "ACERVO/edit_editora.html", context)
 

# --- Exclusão de Registros ---
@login_required
# Corrigido: Permissão alterada de 'delete_livroautor' para 'delete_autor' por motivos de segurança
@permission_required('ACERVO.delete_autor', raise_exception=True)
def deletar_autor(request, autor_id):
    autor = get_object_or_404(Autor, id=autor_id)
    autor.delete()
    return redirect('autores')