import os
import django

# Configura o ambiente Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User

# Cria o usuário 'admin' se ele não existir
try:
    if not User.objects.filter(username='admin').exists():
        print("--- CRIANDO SUPERUSUÁRIO... ---")
        # ATENÇÃO: A senha será 'admin123'. Mude depois no painel se quiser.
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("✅ Superusuário 'admin' criado com sucesso! Senha: admin123")
    else:
        print("⚠️ Superusuário 'admin' já existe. Nada a fazer.")
except Exception as e:
    print(f"❌ Erro ao criar superusuário: {e}")
