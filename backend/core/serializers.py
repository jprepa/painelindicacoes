from rest_framework import serializers
from .models import Parceiro, HistoricoPontuacao

class HistoricoSerializer(serializers.ModelSerializer):
    data_formatada = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoPontuacao
        fields = ['id', 'data', 'data_formatada', 'tipo', 'pontos', 'descricao']

    def get_data_formatada(self, obj):
        return obj.data.strftime('%d/%m/%Y')

class ParceiroSerializer(serializers.ModelSerializer):
    historico = HistoricoSerializer(many=True, read_only=True)
    estados_lista = serializers.SerializerMethodField()
    servicos_lista = serializers.SerializerMethodField()
    
    score_atual = serializers.DecimalField(source='score_real', max_digits=10, decimal_places=2, read_only=True)
    vencimento_info = serializers.ReadOnlyField(source='proximo_vencimento')
    
    # --- A CORREÇÃO DO SELO ---
    status = serializers.ReadOnlyField() # <--- ADICIONE ISSO! Força o envio do status calculado

    class Meta:
        model = Parceiro
        fields = '__all__'

    def get_estados_lista(self, obj):
        if obj.estados_atuacao:
            return [e.strip() for e in obj.estados_atuacao.split(',') if e.strip()]
        return []

    def get_servicos_lista(self, obj):
        if obj.servicos:
            return [s.strip() for s in obj.servicos.split(',') if s.strip()]
        return []
