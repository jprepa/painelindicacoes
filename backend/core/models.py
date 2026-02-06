from django.db import models
from django.utils import timezone
from datetime import timedelta

class Parceiro(models.Model):
    empresa = models.CharField(max_length=255)
    contato_nome = models.CharField(max_length=255, blank=True, null=True)
    
    # Novos Campos de Contato
    email = models.EmailField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=50, blank=True, null=True)
    
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estados_atuacao = models.CharField(max_length=255, blank=True, null=True)
    servicos = models.TextField(blank=True, null=True)
    
    score_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    ultima_indicacao = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.empresa

    @property
    def score_real(self):
        """Calcula o score somando APENAS indicações dos últimos 90 dias"""
        data_limite = timezone.now().date() - timedelta(days=90)
        total = self.historico.filter(data__gte=data_limite).aggregate(models.Sum('pontos'))['pontos__sum']
        return total or 0.00

    @property
    def proximo_vencimento(self):
        """Calcula expiração agrupando por dia (Soma pontos do lote)"""
        data_limite = timezone.now().date() - timedelta(days=90)
        
        # 1. Pega a data da indicação mais antiga que AINDA é válida
        primeira_indicao = self.historico.filter(data__gte=data_limite).order_by('data').first()

        if primeira_indicao:
            data_do_lote = primeira_indicao.data
            
            # 2. Soma TODOS os pontos que foram feitos nesse mesmo dia
            total_pontos_lote = self.historico.filter(data=data_do_lote).aggregate(models.Sum('pontos'))['pontos__sum']
            
            data_expiracao = data_do_lote + timedelta(days=90)
            dias_restantes = (data_expiracao - timezone.now().date()).days
            
            return {
                "dias": max(dias_restantes, 0),
                "pontos": total_pontos_lote, # Retorna a SOMA (ex: 4.80)
                "data_vencimento": data_expiracao
            }
        return None

    @property
    def status(self):
        s = float(self.score_real)
        if s >= 6.1: return "Diamante"
        if s >= 3.4: return "Ouro"
        if s >= 2.4: return "Prata"
        if s >= 1.7: return "Bronze"
        return "Em análise"

class HistoricoPontuacao(models.Model):
    parceiro = models.ForeignKey(Parceiro, related_name='historico', on_delete=models.CASCADE)
    data = models.DateField(auto_now_add=True)
    tipo = models.CharField(max_length=50) 
    pontos = models.DecimalField(max_digits=5, decimal_places=2)
    descricao = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.parceiro} - {self.pontos} ({self.data})"
