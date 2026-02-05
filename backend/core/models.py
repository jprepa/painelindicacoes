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
    
    # --- NOVO CAMPO: ÁREA DE ATUAÇÃO ---
    # Ex: "SP, RJ, MG" (facilitará o filtro no frontend)
    estados_atuacao = models.CharField(max_length=200, blank=True, default="", help_text="Siglas dos estados separadas por vírgula (Ex: SP, RJ)")

    # Status e Score
    status = models.CharField(max_length=20, choices=NIVEIS, default='Bronze')
    score_atual = models.DecimalField(max_digits=10, decimal_places=1, default=0.0)
    ultima_indicacao = models.DateField(default=timezone.now)
    
    # Serviços (Mantido, mas vamos criar uma propriedade para ajudar o React)
    servicos = models.TextField(blank=True, help_text="Separe os serviços por vírgula")

    def __str__(self):
        return self.empresa

    # --- CÉREBRO AUTOMÁTICO ---
    def save(self, *args, **kwargs):
        pontos = float(self.score_atual)
        
        # Regras de Nível
        if pontos < 2.0:
            self.status = 'Bronze'
        elif pontos < 3.5:
            self.status = 'Prata'
        elif pontos < 6.1:
            self.status = 'Ouro'
        else:
            self.status = 'Diamante'
            
        super().save(*args, **kwargs)

    # --- HELPERS PARA O FRONTEND (REACT) ---
    # Transforma "Conciergerie, Vendas" em ['Conciergerie', 'Vendas']
    @property
    def servicos_lista(self):
        if not self.servicos: return []
        return [s.strip() for s in self.servicos.split(',')]

    # Transforma "SP, RJ" em ['SP', 'RJ']
    @property
    def estados_lista(self):
        if not self.estados_atuacao: return []
        return [e.strip() for e in self.estados_atuacao.split(',')]

    # --- CÁLCULOS VISUAIS ---
    @property
    def dias_sem_indicar(self):
        if not self.ultima_indicacao: return 0
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


# --- NOVA TABELA: HISTÓRICO DE PONTUAÇÃO ---
# Isso cria uma lista de movimentações para cada parceiro
class HistoricoPontuacao(models.Model):
    parceiro = models.ForeignKey(Parceiro, on_delete=models.CASCADE, related_name='historico')
    data = models.DateTimeField(auto_now_add=True) # Data automática do lançamento
    tipo = models.CharField(max_length=50) # "Venda" ou "Indicação"
    pontos = models.DecimalField(max_digits=5, decimal_places=2)
    descricao = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-data'] # Mostra sempre o mais recente primeiro

    def __str__(self):
        return f"{self.tipo} - {self.parceiro.empresa} ({self.data})"
