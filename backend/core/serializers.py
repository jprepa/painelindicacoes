from rest_framework import serializers
from .models import Parceiro

class ParceiroSerializer(serializers.ModelSerializer):
    # Avisa que esses campos são calculados na hora (não salvos no banco)
    dias_sem_indicar = serializers.ReadOnlyField()
    multa_estimada = serializers.ReadOnlyField()
    score_futuro = serializers.ReadOnlyField()
    servicos_lista = serializers.SerializerMethodField()

    class Meta:
        model = Parceiro
        fields = '__all__'

    def get_servicos_lista(self, obj):
        # Transforma o texto "BIM, Orçamento" em uma lista real ["BIM", "Orçamento"]
        if obj.servicos:
            return [x.strip() for x in obj.servicos.split(',')]
        return []