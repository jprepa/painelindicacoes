import pandas as pd
import requests
import json
import re
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Parceiro
from .serializers import ParceiroSerializer

# --- IMPORTANTE: Importe a função que criamos no services.py ---
from .services import buscar_cnpjs_pipedrive 

# DDDs para desempate
DDD_ESTADOS = {
    '11': 'SP', '12': 'SP', '13': 'SP', '19': 'SP', '21': 'RJ', '22': 'RJ', '24': 'RJ',
    '31': 'MG', '32': 'MG', '41': 'PR', '42': 'SC', '43': 'RS', '47': 'SC', '48': 'SC',
    '51': 'RS', '61': 'DF', '62': 'GO', '71': 'BA', '81': 'PE', '91': 'PA'
}

class ParceiroViewSet(viewsets.ModelViewSet):
    queryset = Parceiro.objects.all().order_by('-score_atual')
    serializer_class = ParceiroSerializer

    @action(detail=True, methods=['post'])
    def registrar_indicacao(self, request, pk=None):
        pass

    # --- AGENTE DE LEADS 3.0 (Com Pipedrive + Upload de Base + Google + BrasilAPI) ---
    @action(detail=False, methods=['post'])
    def qualificar_leads(self, request):
        # 1. Recebe os arquivos
        file_leads = request.FILES.get('file')
        file_clientes = request.FILES.get('file_clientes') 

        if not file_leads:
            return Response({"erro": "Arquivo de leads não enviado"}, status=400)

        # ---------------------------------------------------------
        # NOVO: CONSULTA O PIPEDRIVE (Carrega tudo na memória antes)
        # ---------------------------------------------------------
        TOKEN_PIPEDRIVE = "952556ce51a1938462a38091c1ea9dfb38b8351c" # Seu Token
        print("--- Consultando Pipedrive (Negócios em Aberto) ---")
        
        # Chama a função do services.py e guarda os CNPJs num conjunto (set)
        cnpjs_em_aberto_crm = buscar_cnpjs_pipedrive(TOKEN_PIPEDRIVE)
        print(f"Pipedrive carregado: {len(cnpjs_em_aberto_crm)} negócios em aberto encontrados.")
        # ---------------------------------------------------------

        # 2. Processa a Base de Clientes (Arquivo manual, se enviado)
        set_clientes_cnpjs = set()
        if file_clientes:
            try:
                df_cli = pd.read_excel(file_clientes)
                indice_coluna = 1 if len(df_cli.columns) > 1 else 0
                coluna_cnpjs = df_cli.iloc[:, indice_coluna].astype(str)
                set_clientes_cnpjs = set(coluna_cnpjs.apply(lambda x: re.sub(r'\D', '', x)))
                print(f"Base manual de clientes carregada: {len(set_clientes_cnpjs)} registros.")
            except Exception as e:
                print(f"Erro ao ler base de clientes manual: {e}")

        # 3. Lê os Leads
        try:
            df = pd.read_excel(file_leads)
        except:
             return Response({"erro": "Arquivo de leads inválido"}, status=400)

        if len(df.columns) < 5:
            return Response({"erro": "Planilha de leads fora do padrão (Min 5 colunas)"}, status=400)
            
        coluna_empresa = df.columns[4] # Coluna E
        coluna_telefone = df.columns[2] # Coluna C

        # SUA CHAVE DO SERPER
        API_KEY = "5857e258a648118c2bc2d3c11f27ec1c54126b96" 
        headers_serper = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
        url_search = "https://google.serper.dev/search"

        print("--- Iniciando Qualificação Linha a Linha ---")

        for index, row in df.iterrows():
            empresa = str(row[coluna_empresa])
            telefone_bruto = str(row[coluna_telefone])
            
            # --- BUSCA CNPJ NO GOOGLE ---
            cnpj_final = "Não encontrado"
            cnpj_numeros = ""
            
            ddd_lead = ''.join(filter(str.isdigit, telefone_bruto))[:2]
            estado_lead = DDD_ESTADOS.get(ddd_lead, "")

            try:
                payload = json.dumps({"q": f"{empresa} CNPJ", "num": 5})
                response = requests.post(url_search, headers=headers_serper, data=payload)
                results = response.json().get("organic", [])
                
                candidatos = []
                for res in results:
                    texto = (res.get("title", "") + " " + res.get("snippet", "")).upper()
                    achados = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
                    for cnpj in achados:
                        score = 0
                        if "CONSTRU" in texto or "ENGENHARIA" in texto: score += 2
                        if estado_lead and estado_lead in texto: score += 3
                        candidatos.append({'cnpj': cnpj, 'score': score})

                if candidatos:
                    candidatos.sort(key=lambda x: x['score'], reverse=True)
                    cnpj_final = candidatos[0]['cnpj']
                    cnpj_numeros = re.sub(r'\D', '', cnpj_final) # Limpa pontos e traços
            except:
                pass

            # --- CONSULTA BRASIL API ---
            atividade_principal = "Não verificada"
            atividades_secundarias = ""
            
            if cnpj_numeros:
                try:
                    url_brasil = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_numeros}"
                    resp_cnpj = requests.get(url_brasil, timeout=5)
                    
                    if resp_cnpj.status_code == 200:
                        dados_cnpj = resp_cnpj.json()
                        atividade_principal = dados_cnpj.get('cnae_fiscal_descricao', 'Não informado')
                        
                        lista_sec = dados_cnpj.get('cnaes_secundarios', [])
                        descricoes_sec = [item.get('descricao', '') for item in lista_sec]
                        atividades_secundarias = "; ".join(descricoes_sec)
                        
                        if len(atividades_secundarias) > 3000:
                            atividades_secundarias = atividades_secundarias[:3000] + "..."
                    else:
                        atividade_principal = "CNPJ não encontrado na Base"
                except:
                    atividade_principal = "Erro API"

            # ---------------------------------------------------------
            # VERIFICAÇÕES DE CLIENTE E CRM
            # ---------------------------------------------------------
            
            # 1. Verifica na planilha manual de clientes
            ja_e_cliente = "NÃO"
            if cnpj_numeros and cnpj_numeros in set_clientes_cnpjs:
                ja_e_cliente = "SIM - JÁ NA BASE (Arquivo)"

            # 2. NOVO: Verifica no PIPEDRIVE
            status_crm = "Disponível" # Padrão
            if cnpj_numeros and cnpj_numeros in cnpjs_em_aberto_crm:
                status_crm = "EM ABERTO (Duplicado)"
            # ---------------------------------------------------------

            # --- SITE e TIPOLOGIA ---
            site_final = "Não encontrado"
            try:
                payload = json.dumps({"q": f"{empresa} site oficial construtora", "num": 1})
                response = requests.post(url_search, headers=headers_serper, data=payload)
                if response.json().get("organic"):
                    site_final = response.json().get("organic")[0].get("link")
            except: pass

            tipologia = "nao_identificado"
            texto_analise = (empresa + " " + site_final + " " + atividade_principal).lower()
            if any(x in texto_analise for x in ['lote', 'bairro', 'urbanismo', 'horizontal']): tipologia = "loteamento_ou_horizontais"
            elif any(x in texto_analise for x in ['edific', 'tower', 'residencial', 'incorp']): tipologia = "residencial_vertical"
            elif any(x in texto_analise for x in ['industria', 'galpao', 'logist']): tipologia = "industrial"

            # --- SALVA TUDO NO DATAFRAME ---
            df.at[index, 'CNPJ Encontrado'] = cnpj_final
            df.at[index, 'Atividade Principal'] = atividade_principal
            df.at[index, 'Atividades Secundarias'] = atividades_secundarias
            df.at[index, 'Site'] = site_final
            df.at[index, 'Tipologia'] = tipologia
            
            # Colunas de validação
            df.at[index, 'Status Cliente'] = ja_e_cliente
            df.at[index, 'Status CRM'] = status_crm # <--- COLUNA NOVA AQUI

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=leads_qualificados_pipedrive.xlsx'
        df.to_excel(response, index=False)
        return response
