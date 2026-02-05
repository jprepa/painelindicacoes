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

# Importa o services atualizado
from .services import buscar_dados_pipedrive 

# DDDs para desempate
DDD_ESTADOS = {
    '11': 'SP', '12': 'SP', '13': 'SP', '19': 'SP', '21': 'RJ', '22': 'RJ', '24': 'RJ',
    '31': 'MG', '32': 'MG', '41': 'PR', '42': 'SC', '43': 'RS', '47': 'SC', '48': 'SC',
    '51': 'RS', '61': 'DF', '62': 'GO', '71': 'BA', '81': 'PE', '91': 'PA'
}

# --- FUNÇÕES AUXILIARES DE CNPJ ---
def calcular_digito(cnpj_parcial):
    """Calcula um dígito verificador do CNPJ (Algoritmo Módulo 11)"""
    tamanho = len(cnpj_parcial)
    if tamanho == 12:
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    else:
        pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = 0
    for i, digito in enumerate(cnpj_parcial):
        soma += int(digito) * pesos[i]
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)

def garantir_cnpj_matriz(cnpj_sujo):
    """Recebe filial ou matriz, retorna sempre a MATRIZ (0001) com DV recalculado."""
    cnpj_limpo = re.sub(r'\D', '', str(cnpj_sujo))
    # Se faltar zero a esquerda vindo do Google (raro, mas possível), ajusta
    cnpj_limpo = cnpj_limpo.zfill(14) 
    
    if len(cnpj_limpo) < 8: return ""

    raiz = cnpj_limpo[:8]
    cnpj_sem_dv = raiz + "0001"
    dv1 = calcular_digito(cnpj_sem_dv)
    dv2 = calcular_digito(cnpj_sem_dv + dv1)
    
    return cnpj_sem_dv + dv1 + dv2
# ----------------------------------

class ParceiroViewSet(viewsets.ModelViewSet):
    queryset = Parceiro.objects.all().order_by('-score_atual')
    serializer_class = ParceiroSerializer

    @action(detail=True, methods=['post'])
    def registrar_indicacao(self, request, pk=None):
        pass

    # --- AGENTE DE LEADS 7.0 (Blindado: Zeros + Coluna Inteligente + Matriz) ---
    @action(detail=False, methods=['post'])
    def qualificar_leads(self, request):
        file_leads = request.FILES.get('file')
        file_clientes = request.FILES.get('file_clientes') 

        if not file_leads: return Response({"erro": "Arquivo de leads não enviado"}, status=400)

        # 1. CARREGA PIPEDRIVE
        TOKEN_PIPEDRIVE = "952556ce51a1938462a38091c1ea9dfb38b8351c" 
        print("--- Consultando Pipedrive ---")
        crm_por_cnpj, crm_por_nome = buscar_dados_pipedrive(TOKEN_PIPEDRIVE)
        print(f"CRM Indexado: {len(crm_por_cnpj)} CNPJs.")

        # 2. PROCESSA BASE DE CLIENTES (COM CORREÇÃO DE ZEROS E COLUNA)
        set_clientes_cnpjs = set()
        if file_clientes:
            try:
                # Lê forçando texto para não perder dados
                df_cli = pd.read_excel(file_clientes, dtype=str)
                
                # --- Lógica Inteligente de Coluna ---
                coluna_alvo = df_cli.columns[0] # Padrão: Coluna A
                for col in df_cli.columns:
                    # Procura por "CNPJ" ou "CPF" no cabeçalho
                    if "CNPJ" in str(col).upper() or "CPF" in str(col).upper():
                        coluna_alvo = col
                        break
                
                print(f"Lendo Clientes da coluna: {coluna_alvo}")
                
                # Pega a coluna e aplica a blindagem (zfill)
                set_clientes_cnpjs = set(
                    df_cli[coluna_alvo].astype(str)
                    .apply(lambda x: re.sub(r'\.0$', '', x)) # Remove .0
                    .apply(lambda x: re.sub(r'\D', '', x))   # Remove traços
                    .apply(lambda x: x.zfill(14)[:8])        # <--- O SEGREDO: Preenche zeros e pega raiz
                )
                set_clientes_cnpjs.discard('') 
                print(f"Base Clientes: {len(set_clientes_cnpjs)} raízes carregadas.")
            except Exception as e:
                print(f"Erro Base Clientes: {e}")

        # 3. LÊ OS LEADS
        try: df = pd.read_excel(file_leads)
        except: return Response({"erro": "Arquivo inválido"}, status=400)
        if len(df.columns) < 5: return Response({"erro": "Colunas insuficientes"}, status=400)
            
        coluna_empresa = df.columns[4] 
        coluna_telefone = df.columns[2]

        API_KEY = "5857e258a648118c2bc2d3c11f27ec1c54126b96"
        headers_serper = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
        url_search = "https://google.serper.dev/search"

        for index, row in df.iterrows():
            empresa_nome = str(row[coluna_empresa]).strip()
            telefone_bruto = str(row[coluna_telefone])
            
            # --- BUSCA E FORÇA MATRIZ ---
            cnpj_matriz_final = ""
            ddd_lead = ''.join(filter(str.isdigit, telefone_bruto))[:2]
            estado_lead = DDD_ESTADOS.get(ddd_lead, "")

            try:
                payload = json.dumps({"q": f"{empresa_nome} CNPJ", "num": 5})
                response = requests.post(url_search, headers=headers_serper, data=payload)
                results = response.json().get("organic", [])
                
                candidatos = []
                for res in results:
                    texto = (res.get("title", "") + " " + res.get("snippet", "")).upper()
                    achados = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
                    
                    for cnpj_achado in achados:
                        # Converte Filial -> Matriz
                        cnpj_convertido = garantir_cnpj_matriz(cnpj_achado)
                        
                        score = 0
                        if "CONSTRU" in texto or "ENGENHARIA" in texto: score += 2
                        if estado_lead and estado_lead in texto: score += 3
                        candidatos.append({'cnpj': cnpj_convertido, 'score': score})

                if candidatos:
                    candidatos.sort(key=lambda x: x['score'], reverse=True)
                    cnpj_matriz_final = candidatos[0]['cnpj']
            except: pass

            # --- BRASIL API ---
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
                    else: atividade = "CNPJ não encontrado na Base"
                except: pass

            # --- VALIDAÇÕES FINAIS ---
            status_crm = "Disponível"
            contato_crm = ""
            links_crm = ""
            status_cliente = "NÃO"

            if cnpj_matriz_final:
                # CRM
                if cnpj_matriz_final in crm_por_cnpj:
                    matches = crm_por_cnpj[cnpj_matriz_final]
                    status_crm = "EM ABERTO (Match CNPJ)"
                    contato_crm = ", ".join({m['contato'] for m in matches})
                    links_crm = " | ".join([m['link'] for m in matches])
                
                # CLIENTES (Compara Raízes: 8 dígitos)
                raiz_encontrada = cnpj_matriz_final[:8]
                if raiz_encontrada in set_clientes_cnpjs:
                    status_cliente = "SIM - JÁ NA BASE"

            # Fallback CRM por Nome
            if status_crm == "Disponível" and empresa_nome.lower() in crm_por_nome:
                matches = crm_por_nome[empresa_nome.lower()]
                status_crm = "EM ABERTO (Match Nome)"
                contato_crm = ", ".join({m['contato'] for m in matches})
                links_crm = " | ".join([m['link'] for m in matches])

            # --- SITE e TIPOLOGIA ---
            site_final = "Não encontrado"
            try:
                p_site = json.dumps({"q": f"{empresa_nome} site oficial", "num": 1})
                r_site = requests.post(url_search, headers=headers_serper, data=p_site)
                if r_site.json().get("organic"):
                    site_final = r_site.json().get("organic")[0].get("link")
            except: pass

            tipologia = "nao_identificado"
            txt = (empresa_nome + " " + site_final + " " + atividade).lower()
            if any(x in txt for x in ['lote', 'bairro', 'urbanismo']): tipologia = "loteamento"
            elif any(x in txt for x in ['edific', 'residencial', 'incorp']): tipologia = "vertical"
            elif any(x in txt for x in ['industria', 'galpao']): tipologia = "industrial"

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
        response['Content-Disposition'] = 'attachment; filename=leads_qualificados_final.xlsx'
        df.to_excel(response, index=False)
        return response
