from django.shortcuts import render, redirect, get_object_or_404
from .models import Autor, Categoria, Editora, Livro, Aluno, Emprestimo
from .forms import AutorForm, CategoriaForm, EditoraForm, LivroForm, LivroAutorForm
from django.http import Http404
from django.contrib.auth.decorators import login_required, permission_required
from datetime import date, timedelta
from functools import wraps
from django.utils import timezone
from django.contrib import messages
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import Count
from django.core.mail import EmailMessage
from django.utils.html import strip_tags

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
            return redirect('autores')
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
            return redirect('categorias')
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
            return redirect('editoras')
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
        form = LivroForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('livros')
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
            return redirect('livros')
    context = {'form': form}
    return render(request, "ACERVO/new_livro_autor.html", context)


# --- Empréstimos ---
@login_required
def meus_emprestimos(request):
    aluno = Aluno.objects.filter(user=request.user).first()
    emprestimos = Emprestimo.objects.filter(aluno=aluno)
    hoje = timezone.localdate()
    
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
    # 1. Busca o livro e o aluno logado
    livro = get_object_or_404(Livro, id=livro_id)
    aluno = Aluno.objects.filter(user=request.user).first()
    
    if not aluno:
        messages.error(request, "Você precisa ser um aluno cadastrado para realizar empréstimos.")
        return redirect('livros')

    # 2. Verifica se já existe um empréstimo ativo para este livro
    emprestimo_ativo = Emprestimo.objects.filter(aluno=aluno, livro=livro, devolvido=False).exists()
    
    if emprestimo_ativo:
        messages.error(request, "Você já tem um empréstimo ativo com esse livro.")
        return redirect('meus_emprestimos')

    # 3. Cria o empréstimo diretamente ao receber o POST (sem formulário)
    if request.method == 'POST':
        hoje = timezone.localdate()
        
        Emprestimo.objects.create(
            aluno=aluno,
            livro=livro,
            valor=livro.valor,
            data_emprestimo=hoje,
            data_devolucao=hoje + timedelta(days=7),
            devolvido=False
        )

        messages.success(request, f"Empréstimo do '{livro.nome}' realizado com sucesso!")
        return redirect('meus_emprestimos')
        
    # Se tentarem acessar a URL por GET, apenas redireciona de volta
    return redirect('livros')
@login_required
def renovar_emprestimo(request, livro_id):
    aluno = Aluno.objects.filter(user=request.user).first()
    livro = get_object_or_404(Livro, id=livro_id)
    emprestimo = Emprestimo.objects.filter(aluno=aluno, livro=livro, devolvido=False).first()

    if emprestimo:
        if emprestimo.renovacoes < Emprestimo.MAXIMO_RENOVACOES:
            hoje = timezone.localdate()
            
            # 1. VALIDAÇÃO DE ATRASO
            if hoje > emprestimo.data_devolucao:
                messages.error(request, "Não é possível renovar um livro que já está atrasado.")
                return redirect('meus_emprestimos')
            
            # 2. CÁLCULO DOS INTERVALOS DE TRAVA (5 DIAS)
            if emprestimo.renovacoes == 0:
                # Primeira renovação: calcula a partir da data de empréstimo original
                intervalo = (hoje - emprestimo.data_emprestimo).days
                if intervalo <= 5:
                    messages.warning(
                        request, 
                        f"Você fez o empréstimo desse livro há {intervalo} dia(s). Só poderá renovar após 5 dias."
                    )
                    return redirect('meus_emprestimos')
            else:
                # Renovações seguintes: descobrimos a data teórica da última renovação
                # Subtraímos 7 dias da devolução atual para achar o início do período atual
                data_base = emprestimo.data_ultima_renovacao if emprestimo.renovacoes > 0 else emprestimo.data_emprestimo
                intervalo_two = (hoje - data_base).days
                
                if intervalo_two <= 5:
                    messages.warning(
                        request, 
                        f"Você já renovou este livro há {intervalo_two} dia(s). É necessário aguardar pelo menos 5 dias para renovar novamente."
                    )
                    return redirect('meus_emprestimos')

            # 3. SE PASSOU NAS VALIDAÇÕES, EXECUTA A RENOVAÇÃO
            emprestimo.data_devolucao += timedelta(days=7)
            emprestimo.valor = (emprestimo.valor or 0) + livro.valor
            emprestimo.renovacoes += 1
            emprestimo.data_ultima_renovacao = hoje
            emprestimo.save()
            
            messages.success(
                request,
                f"O empréstimo do livro '{livro.nome}' foi renovado por mais 7 dias! "
                f"({emprestimo.renovacoes}/{Emprestimo.MAXIMO_RENOVACOES})"
            )
        else:
            messages.error(
                request,
                f"Você já atingiu o limite máximo de {Emprestimo.MAXIMO_RENOVACOES} renovações para este livro."
            )
    else:
        messages.error(request, "Você não possui um empréstimo ativo deste livro para renovar.")

    return redirect('meus_emprestimos')

@login_required
@licenca_valida
def visualizar_pdf(request, livro_id):
    aluno = Aluno.objects.filter(user=request.user).first()
        
    livro = get_object_or_404(Livro, id=livro_id)
    emprestimo = Emprestimo.objects.filter(aluno=aluno, livro=livro, devolvido=False).first()
    
    if not emprestimo:
        messages.error(request, "Você precisa ter um empréstimo ativo para visualizar este livro.")
        return redirect('meus_emprestimos')
        
    return render(request, "ACERVO/visualizar_pdf.html", {'livro': livro, 'emprestimo': emprestimo})


# --- Mecanismo de Busca ---
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
            return redirect('autores')
        
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
            return redirect('categorias')
        
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
            form.save()  # CORREÇÃO: Agora o formulário salva a edição!
            return redirect('editoras')
        
    context = {'editora': editora, 'form': form}
    return render(request, "ACERVO/edit_editora.html", context)
 

# --- Exclusão de Registros ---
@login_required
@permission_required('ACERVO.delete_autor', raise_exception=True)
def deletar_autor(request, autor_id):
    autor = get_object_or_404(Autor, id=autor_id)
    autor.delete()
    return redirect('autores')


def enviar_email(destinatario, assunto, mensagem):
    # 1. Fazemos o replace FORA da f-string para evitar o erro de sintaxe
    mensagem_html = mensagem.replace('\n', '<br>')
    
    # 2. Agora criamos o HTML usando a nova variável sem barras dentro das chaves
    html_conteudo = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2C3E50; border-bottom: 2px solid #2C3E50; padding-bottom: 10px;">Biblioteca do Python</h2>
                <p style="font-size: 16px;">{mensagem_html}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #7f8c8d;">Este é um e-mail automático do sistema. Por favor, não responda a esta mensagem.</p>
            </div>
        </body>
    </html>
    """
    
    email = EmailMessage(
        subject=assunto,
        body=html_conteudo,
        # AJUSTE 1: Alterado para o e-mail cadastrado no MailerLite
        from_email="Sistema Biblioteca <dev.cesar26@gmail.com>",
        to=[destinatario],
        # AJUSTE 2: Alterado o reply_to para o mesmo e-mail para manter a consistência
        reply_to=["dev.cesar26@gmail.com"],
    )
    
    email.content_subtype = "html" 
    email.send(fail_silently=False)

