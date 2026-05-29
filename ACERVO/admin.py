from django.contrib import admin
from django.apps import apps
from unfold.admin import ModelAdmin 

# 1. Sua classe base do Unfold para modernizar o visual
class BaseAdmin(ModelAdmin):
    pass

# 2. Pega as configurações apenas do seu app ACERVO
app_config = apps.get_app_config('ACERVO')

# 3. Registra de forma automatizada apenas os SEUS modelos
for model in app_config.get_models():
    # Isso evita registrar tabelas intermediárias automáticas (como as de ManyToMany), se houverem
    if not model._meta.auto_created:
        admin.site.register(model, BaseAdmin)
