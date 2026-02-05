from rest_framework import serializers
from .models import Parceiro, HistoricoPontuacao

class HistoricoSerializer(serializers.ModelSerializer):
    data_formatada = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoPontuacao
        fields = ['id', 'tipo', 'pontos', 'data_formatada', 'descricao']

    def get_data_formatada(self, obj):
        return obj.data.strftime('%d/%m/%Y')

class ParceiroSerializer(serializers.ModelSerializer):
    servicos_lista = serializers.ReadOnlyField()
    estados_lista = serializers.ReadOnlyField() # NOVO
    status = serializers.ReadOnlyField()
    # Traz o histórico aninhado
    historico = HistoricoSerializer(many=True, read_only=True) 

    class Meta:
        model = Parceiro
        fields = '__all__'

    def get_servicos_lista(self, obj):
        # Transforma o texto "BIM, Orçamento" em uma lista real ["BIM", "Orçamento"]
        if obj.servicos:
            return [x.strip() for x in obj.servicos.split(',')]
        return []
