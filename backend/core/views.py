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
from .services import buscar_dados_pipedrive 

# DDDs para desempate
DDD_ESTADOS = {
    '11': 'SP', '12': 'SP', '13': 'SP', '19': 'SP', '21': 'RJ', '22': 'RJ', '24': 'RJ',
    '31': 'MG', '32': 'MG', '41': 'PR', '42': 'SC', '43': 'RS', '47': 'SC', '48': 'SC',
    '51': 'RS', '61': 'DF', '62': 'GO', '71': 'BA', '81': 'PE', '91': 'PA'
}

# --- FUNÇÕES DE LIMPEZA E CNPJ ---
def limpar_valor_paranoico(valor):
    """
    Remove notação científica (1.23E+13), pontos, traços e espaços.
    Retorna apenas os números em formato string.
    """
    if pd.isna(valor): return ""
    s_val = str(valor).strip()
    
    # Se tiver "E+" ou "e+" (Notação Científica), tenta converter float -> int -> str
    if 'E' in s_val.upper():
        try:
            # Converte '1.23E+13' para float, depois int para tirar .0, depois str
            s_val = '{:.0f}'.format(float(s_val))
        except:
            pass # Se der erro, segue a vida
            
    # Remove .0 no final se sobrar
    if s_val.endswith('.0'): s_val = s_val[:-2]
    
    # Remove tudo que não for dígito
    return re.sub(r'\D', '', s_val)

def calcular_digito(cnpj_parcial):
    tamanho = len(cnpj_parcial)
    pesos = [5,4,3,2,9,8,7,6,5,4,3,2] if tamanho == 12 else [6,5,4,3,2,9,8,7,6,5,4,3,2]
    soma = sum(int(d) * pesos[i] for i, d in enumerate(cnpj_parcial))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)

def garantir_cnpj_matriz(cnpj_sujo):
    # Limpa
    cnpj_limpo = limpar_valor_paranoico(cnpj_sujo)
    cnpj_limpo = cnpj_limpo.zfill(14) # Garante tamanho minimo
    
    if len(cnpj_limpo) < 8: return ""

    raiz = cnpj_limpo[:8]
    cnpj_sem_dv = raiz + "0001"
    dv1 = calcular_digito(cnpj_sem_dv)
    dv2 = calcular_digito(cnpj_sem_dv + dv1)
    return cnpj_sem_dv + dv1 + dv2
# ---------------------------------

class ParceiroViewSet(viewsets.ModelViewSet):
    queryset = Parceiro.objects.all().order_by('-score_atual')
    serializer_class = ParceiroSerializer

@action(detail=True, methods=['post'])
    def registrar_indicacao(self, request, pk=None):
        parceiro = self.get_object()
        
        # Pega os dados enviados pelo React
        pontos = request.data.get('pontos')
        tipo = request.data.get('tipo', 'Indicação') # Se não mandar, assume Indicação
        
        if not pontos:
            return Response({"erro": "Pontos obrigatórios"}, status=400)

        # 1. Cria o registro no histórico
        HistoricoPontuacao.objects.create(
            parceiro=parceiro,
            tipo=tipo,
            pontos=pontos,
            descricao=f"Lançamento manual via painel"
        )

        # 2. Atualiza o Score do Parceiro
        from decimal import Decimal
        parceiro.score_atual += Decimal(str(pontos))
        
        # Atualiza a data da última indicação
        from django.utils import timezone
        parceiro.ultima_indicacao = timezone.now().date()
        
        parceiro.save()

        # Retorna o parceiro atualizado com o novo histórico
        serializer = self.get_serializer(parceiro)
        return Response(serializer.data)

    # --- AGENTE DE LEADS 9.0 (CSI MODE: Paranóico + Logs) ---
    @action(detail=False, methods=['post'])
    def qualificar_leads(self, request):
        file_leads = request.FILES.get('file')
        file_clientes = request.FILES.get('file_clientes') 

        if not file_leads: return Response({"erro": "Arquivo de leads não enviado"}, status=400)

        # 1. PIPEDRIVE
        TOKEN_PIPEDRIVE = "952556ce51a1938462a38091c1ea9dfb38b8351c"
        print(">>> 1. Carregando Pipedrive...")
        crm_por_cnpj, crm_por_nome = buscar_dados_pipedrive(TOKEN_PIPEDRIVE)
        print(f"    CRM OK: {len(crm_por_cnpj)} CNPJs carregados.")

        # 2. BASE DE CLIENTES (COM LOGS VISUAIS)
        set_clientes_cnpjs = set()
        if file_clientes:
            try:
                print(">>> 2. Lendo Base de Clientes (Modo Paranóico)...")
                # header=None para ler tudo, até cabeçalho, como dado
                df_cli = pd.read_excel(file_clientes, header=None)
                
                valores = df_cli.values.flatten()
                amostra_log = [] # Para mostrar no terminal

                for val in valores:
                    # Limpeza bruta
                    numeros = limpar_valor_paranoico(val)
                    
                    # Filtra lixo (só aceita CPF/CNPJ possíveis)
                    if 8 <= len(numeros) <= 14:
                        # Zfill garante zeros a esquerda. Pega os 8 primeiros (Raiz)
                        raiz = numeros.zfill(14)[:8]
                        set_clientes_cnpjs.add(raiz)
                        
                        if len(amostra_log) < 5: amostra_log.append(f"{val} -> {raiz}")
                
                print(f"    Base Clientes Carregada: {len(set_clientes_cnpjs)} raízes únicas.")
                print(f"    AMOSTRA (Como o código leu seus dados):")
                for item in amostra_log: print(f"      {item}")
                print("    ------------------------------------------------")

            except Exception as e:
                print(f"!!! ERRO NA LEITURA CLIENTES: {e}")

        # 3. LEADS
        try: df = pd.read_excel(file_leads)
        except: return Response({"erro": "Arquivo inválido"}, status=400)
        
        coluna_empresa = df.columns[4] 
        coluna_telefone = df.columns[2]
        
        API_KEY = "5857e258a648118c2bc2d3c11f27ec1c54126b96"
        headers_serper = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
        url_search = "https://google.serper.dev/search"

        print(">>> 3. Iniciando Qualificação...")

        for index, row in df.iterrows():
            empresa_nome = str(row[coluna_empresa]).strip()
            telefone_bruto = str(row[coluna_telefone])
            
            # --- BUSCA GOOGLE (Mantém lógica de matriz) ---
# ... (código anterior: definição de empresa_nome, telefone_bruto, etc) ...

            # --- BUSCA GOOGLE (AGENTE 10.0: Busca Direcionada por Estado) ---
            cnpj_matriz_final = ""
            
            # 1. Descobre o Estado pelo DDD
            ddd_lead = ''.join(filter(str.isdigit, telefone_bruto))[:2]
            estado_lead = DDD_ESTADOS.get(ddd_lead, "")

            try:
                # --- AQUI ESTÁ A MUDANÇA ---
                # Monta a busca: "Nome Empresa + CNPJ + Estado"
                termo_busca = f"{empresa_nome} CNPJ"
                if estado_lead:
                    termo_busca += f" {estado_lead}" # Adiciona " SP", " RJ", etc.
                
                # Manda para o Google (Serper)
                payload = json.dumps({"q": termo_busca, "num": 5})
                response = requests.post(url_search, headers=headers_serper, data=payload)
                results = response.json().get("organic", [])
                
                candidatos = []
                for res in results:
                    texto = (res.get("title", "") + " " + res.get("snippet", "")).upper()
                    achados = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
                    
                    for c_achado in achados:
                        # Converte Filial -> Matriz
                        c_convertido = garantir_cnpj_matriz(c_achado)
                        
                        score = 0
                        # Pontuação extra
                        if "CONSTRU" in texto or "ENGENHARIA" in texto: score += 2
                        
                        # Se o estado apareceu no texto, ganha MAIS pontos ainda
                        if estado_lead and estado_lead in texto: score += 5 
                        
                        candidatos.append({'cnpj': c_convertido, 'score': score})

                if candidatos:
                    # Pega o com maior score
                    candidatos.sort(key=lambda x: x['score'], reverse=True)
                    cnpj_matriz_final = candidatos[0]['cnpj']
                    
            except Exception as e:
                # Opcional: printar erro se quiser debugar
                # print(f"Erro busca Google: {e}")
                pass
            
            # ... (continua para Brasil API igual antes) ...

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

            # --- VALIDAÇÕES ---
            status_crm = "Disponível"
            contato_crm = ""
            links_crm = ""
            status_cliente = "NÃO"
            debug_match = "" # Log para ver erros

            if cnpj_matriz_final:
                # CRM
                if cnpj_matriz_final in crm_por_cnpj:
                    matches = crm_por_cnpj[cnpj_matriz_final]
                    status_crm = "EM ABERTO (Match CNPJ)"
                    contato_crm = ", ".join({m['contato'] for m in matches})
                    links_crm = " | ".join([m['link'] for m in matches])
                
                # CLIENTES (COMPARACAO RAIZ vs RAIZ)
                raiz_lead = cnpj_matriz_final[:8] # 8 digitos
                
                if raiz_lead in set_clientes_cnpjs:
                    status_cliente = "SIM - JÁ NA BASE"
                    debug_match = "MATCH!"
                else:
                    debug_match = f"SEM MATCH ({raiz_lead} nao ta no set)"

            # Fallback CRM Nome
            if status_crm == "Disponível" and empresa_nome.lower() in crm_por_nome:
                matches = crm_por_nome[empresa_nome.lower()]
                status_crm = "EM ABERTO (Match Nome)"
                contato_crm = ", ".join({m['contato'] for m in matches})
                links_crm = " | ".join([m['link'] for m in matches])

            # LOG TEMPORÁRIO NO TERMINAL PARA VOCÊ CONFERIR
            if cnpj_matriz_final:
                print(f"  > {empresa_nome[:20]}... | CNPJ Achado: {cnpj_matriz_final} | Raiz: {cnpj_matriz_final[:8]} | Cliente? {status_cliente}")

            # --- SITE e TIPOLOGIA ---
            site_final = "Não encontrado"
            try:
                p_site = json.dumps({"q": f"{empresa_nome} site oficial", "num": 1})
                r_site = requests.post(url_search, headers=headers_serper, data=p_site)
                if r_site.json().get("organic"): site_final = r_site.json().get("organic")[0].get("link")
            except: pass

            tipologia = "nao_identificado"
            txt = (empresa_nome + " " + site_final + " " + atividade).lower()
            if any(x in txt for x in ['lote', 'bairro', 'urbanismo']): tipologia = "loteamento"
            elif any(x in txt for x in ['edific', 'residencial', 'incorp']): tipologia = "vertical"
            elif any(x in txt for x in ['industria', 'galpao']): tipologia = "industrial"

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
        response['Content-Disposition'] = 'attachment; filename=leads_csi.xlsx'
        df.to_excel(response, index=False)
        return response
