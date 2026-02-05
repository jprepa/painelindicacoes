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

# Importa os serviços do Pipedrive
from .services import buscar_dados_pipedrive 

# DDDs para desempate
DDD_ESTADOS = {
    '11': 'SP', '12': 'SP', '13': 'SP', '19': 'SP', '21': 'RJ', '22': 'RJ', '24': 'RJ',
    '31': 'MG', '32': 'MG', '41': 'PR', '42': 'SC', '43': 'RS', '47': 'SC', '48': 'SC',
    '51': 'RS', '61': 'DF', '62': 'GO', '71': 'BA', '81': 'PE', '91': 'PA'
}

# --- FUNÇÃO NOVA: MATEMÁTICA DO CNPJ ---
def calcular_digito(cnpj_parcial):
    """Calcula um dígito verificador do CNPJ (Algoritmo Módulo 11)"""
    tamanho = len(cnpj_parcial)
    # Pesos: [5,4,3,2,9,8,7,6,5,4,3,2] para o primeiro dígito
    # Pesos: [6,5,4,3,2,9,8,7,6,5,4,3,2] para o segundo
    if tamanho == 12:
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    else:
        pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    soma = 0
    for i, digito in enumerate(cnpj_parcial):
        soma += int(digito) * pesos[i]
    
    resto = soma % 11
    if resto < 2:
        return '0'
    else:
        return str(11 - resto)

def garantir_cnpj_matriz(cnpj_sujo):
    """
    Recebe qualquer CNPJ (filial ou matriz), pega a raiz e retorna 
    o CNPJ da MATRIZ (0001) com os dígitos verificadores recalculados.
    """
    # 1. Limpa tudo que não é número
    cnpj_limpo = re.sub(r'\D', '', str(cnpj_sujo))
    
    # Se não tiver pelo menos 8 dígitos (raiz), retorna vazio
    if len(cnpj_limpo) < 8: return ""

    # 2. Pega só os 8 primeiros dígitos (A Raiz da empresa)
    raiz = cnpj_limpo[:8]
    
    # 3. Adiciona o padrão de Matriz (0001)
    cnpj_sem_dv = raiz + "0001"
    
    # 4. Calcula o primeiro dígito verificador (13º dígito)
    dv1 = calcular_digito(cnpj_sem_dv)
    
    # 5. Calcula o segundo dígito verificador (14º dígito)
    dv2 = calcular_digito(cnpj_sem_dv + dv1)
    
    # Retorna o CNPJ completo da Matriz
    return cnpj_sem_dv + dv1 + dv2
# ---------------------------------------


class ParceiroViewSet(viewsets.ModelViewSet):
    queryset = Parceiro.objects.all().order_by('-score_atual')
    serializer_class = ParceiroSerializer

    @action(detail=True, methods=['post'])
    def registrar_indicacao(self, request, pk=None):
        pass

    # --- AGENTE DE LEADS 6.0 (Força Matriz + Pipedrive Links) ---
    @action(detail=False, methods=['post'])
    def qualificar_leads(self, request):
        file_leads = request.FILES.get('file')
        file_clientes = request.FILES.get('file_clientes') 

        if not file_leads:
            return Response({"erro": "Arquivo de leads não enviado"}, status=400)

        # 1. CARREGA O PIPEDRIVE
        TOKEN_PIPEDRIVE = "952556ce51a1938462a38091c1ea9dfb38b8351c" 
        print("--- Consultando Pipedrive ---")
        crm_por_cnpj, crm_por_nome = buscar_dados_pipedrive(TOKEN_PIPEDRIVE)
        print(f"CRM Indexado: {len(crm_por_cnpj)} CNPJs.")

        # 2. Processa a Base de Clientes (Manual)
        set_clientes_cnpjs = set()
        if file_clientes:
            try:
                df_cli = pd.read_excel(file_clientes)
                idx = 1 if len(df_cli.columns) > 1 else 0
                col = df_cli.iloc[:, idx].astype(str)
                # Guarda apenas a raiz do CNPJ (8 dígitos) para comparar matriz com filial se precisar
                set_clientes_cnpjs = set(col.apply(lambda x: re.sub(r'\D', '', x)[:8]))
                print(f"Base manual: {len(set_clientes_cnpjs)} raízes carregadas.")
            except: pass

        # 3. Lê Leads
        try: df = pd.read_excel(file_leads)
        except: return Response({"erro": "Arquivo inválido"}, status=400)

        if len(df.columns) < 5: return Response({"erro": "Colunas insuficientes"}, status=400)
            
        coluna_empresa = df.columns[4] 
        coluna_telefone = df.columns[2]

        API_KEY = "5857e258a648118c2bc2d3c11f27ec1c54126b96" 
        headers_serper = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
        url_search = "https://google.serper.dev/search"

        print("--- Iniciando ---")

        for index, row in df.iterrows():
            empresa_nome = str(row[coluna_empresa]).strip()
            telefone_bruto = str(row[coluna_telefone])
            
            # --- BUSCA NO GOOGLE ---
            cnpj_matriz_final = "" # Vamos guardar só a matriz aqui
            
            ddd_lead = ''.join(filter(str.isdigit, telefone_bruto))[:2]
            estado_lead = DDD_ESTADOS.get(ddd_lead, "")

            try:
                # Busca focada em CNPJ
                payload = json.dumps({"q": f"{empresa_nome} CNPJ", "num": 5})
                response = requests.post(url_search, headers=headers_serper, data=payload)
                results = response.json().get("organic", [])
                
                candidatos = []
                for res in results:
                    texto = (res.get("title", "") + " " + res.get("snippet", "")).upper()
                    # Acha qualquer CNPJ no texto
                    achados = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
                    
                    for cnpj_achado in achados:
                        # --- AQUI ESTÁ O PULO DO GATO ---
                        # Converte o que achou (mesmo que seja filial) para MATRIZ
                        cnpj_convertido = garantir_cnpj_matriz(cnpj_achado)
                        
                        score = 0
                        if "CONSTRU" in texto or "ENGENHARIA" in texto: score += 2
                        if estado_lead and estado_lead in texto: score += 3
                        
                        candidatos.append({'cnpj': cnpj_convertido, 'score': score})

                if candidatos:
                    candidatos.sort(key=lambda x: x['score'], reverse=True)
                    # Pega o vencedor (já convertido para matriz)
                    cnpj_matriz_final = candidatos[0]['cnpj']
            except: pass

            # --- CONSULTA BRASIL API (Usando o CNPJ Matriz) ---
            atividade = "Não verificada"
            secundarias = ""
            
            if cnpj_matriz_final:
                try:
                    url_brasil = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_matriz_final}"
                    resp = requests.get(url_brasil, timeout=5)
                    
                    if resp.status_code == 200:
                        dados = resp.json()
                        atividade = dados.get('cnae_fiscal_descricao', 'Não informado')
                        sec = [i.get('descricao','') for i in dados.get('cnaes_secundarios', [])]
                        secundarias = "; ".join(sec)[:3000]
                    else:
                        atividade = "CNPJ não encontrado na Base"
                except: pass

            # ---------------------------------------------------------
            # VALIDAÇÃO CRM E CLIENTES
            # ---------------------------------------------------------
            status_crm = "Disponível"
            contato_crm = ""
            links_crm = ""
            status_cliente = "NÃO"

            if cnpj_matriz_final:
                # 1. CRM (Verifica se a MATRIZ está no Pipedrive)
                if cnpj_matriz_final in crm_por_cnpj:
                    matches = crm_por_cnpj[cnpj_matriz_final]
                    status_crm = "EM ABERTO (Match CNPJ)"
                    contato_crm = ", ".join({m['contato'] for m in matches})
                    links_crm = " | ".join([m['link'] for m in matches])
                
                # 2. Clientes (Verifica se a RAIZ do CNPJ está na base de clientes)
                raiz_cnpj = cnpj_matriz_final[:8]
                if raiz_cnpj in set_clientes_cnpjs:
                    status_cliente = "SIM - JÁ NA BASE"

            # Fallback para Nome se não achou por CNPJ
            if status_crm == "Disponível" and empresa_nome.lower() in crm_por_nome:
                matches = crm_por_nome[empresa_nome.lower()]
                status_crm = "EM ABERTO (Match Nome)"
                contato_crm = ", ".join({m['contato'] for m in matches})
                links_crm = " | ".join([m['link'] for m in matches])

            # ---------------------------------------------------------

            # Busca site
            site_final = "Não encontrado"
            try:
                p_site = json.dumps({"q": f"{empresa_nome} site oficial", "num": 1})
                r_site = requests.post(url_search, headers=headers_serper, data=p_site)
                if r_site.json().get("organic"):
                    site_final = r_site.json().get("organic")[0].get("link")
            except: pass

            tipologia = "nao_identificado"
            txt_tipo = (empresa_nome + " " + site_final + " " + atividade).lower()
            if any(x in txt_tipo for x in ['lote', 'bairro', 'urbanismo']): tipologia = "loteamento"
            elif any(x in txt_tipo for x in ['edific', 'residencial', 'incorp']): tipologia = "vertical"
            elif any(x in txt_tipo for x in ['industria', 'galpao']): tipologia = "industrial"

            # Salva
            df.at[index, 'CNPJ Encontrado'] = cnpj_matriz_final
            df.at[index, 'Atividade Principal'] = atividade
            df.at[index, 'Atividades Secundarias'] = secundarias
            df.at[index, 'Site'] = site_final
            df.at[index, 'Tipologia'] = tipologia
            df.at[index, 'Status Cliente'] = status_cliente
            df.at[index, 'Status CRM'] = status_crm
            df.at[index, 'Contato no CRM'] = contato_crm
            df.at[index, 'Link Card Pipedrive'] = links_crm

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=leads_qualificados_matriz.xlsx'
        df.to_excel(response, index=False)
        return response
