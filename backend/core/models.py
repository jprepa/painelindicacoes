from django.db import models
from django.utils import timezone
from datetime import date

class Parceiro(models.Model):
    NIVEIS = (
        ('Bronze', 'Bronze'),
        ('Prata', 'Prata'),
        ('Ouro', 'Ouro'),
        ('Diamante', 'Diamante'),
    )

    empresa = models.CharField(max_length=100)
    contato_nome = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    cidade = models.CharField(max_length=100)
    
    # Status e Score
    status = models.CharField(max_length=20, choices=NIVEIS, default='Bronze')
    score_atual = models.DecimalField(max_digits=10, decimal_places=1, default=0.0) # Aumentei para aceitar 500.0
    ultima_indicacao = models.DateField(default=timezone.now)
    servicos = models.TextField(blank=True, help_text="Separe os serviços por vírgula")

    def __str__(self):
        return self.empresa

    # --- CÉREBRO AUTOMÁTICO (NOVIDADE) ---
    def save(self, *args, **kwargs):
        # Converte para número para garantir a comparação
        pontos = float(self.score_atual)
        
        # DEFINIÇÃO DAS REGRAS (Ajuste esses números conforme sua regra de negócio)
        if pontos < 2.0:
            self.status = 'Bronze'
        elif pontos < 3.5:
            self.status = 'Prata'
        elif pontos < 6.1:
            self.status = 'Ouro'
        else:
            self.status = 'Diamante'
            
        # Salva de verdade
        super().save(*args, **kwargs)

    # --- Cálculos de visualização ---
    @property
    def dias_sem_indicar(self):
        delta = date.today() - self.ultima_indicacao
        return delta.days

    @property
    def multa_estimada(self):
        if self.dias_sem_indicar <= 30: return 0
        if self.status == 'Diamante': return 3
        if self.status == 'Ouro': return 2
        if self.status == 'Prata': return 1
        return 0 

    @property
    def score_futuro(self):
        novo_score = float(self.score_atual) - self.multa_estimada
        return max(0.0, novo_score)