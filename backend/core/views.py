import pandas as pd
import requests
import json
import re
from decimal import Decimal
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Parceiro, HistoricoPontuacao
from .serializers import ParceiroSerializer
from .services import buscar_dados_pipedrive 

# --- CONFIGURAÇÕES ---
TOKEN_PIPEDRIVE = "952556ce51a1938462a38091c1ea9dfb38b8351c"
API_KEY_SERPER = "5857e258a648118c2bc2d3c11f27ec1c54126b96"

DDD_ESTADOS = {
    '11': 'SP', '12': 'SP', '13': 'SP', '19': 'SP', '21': 'RJ', '22': 'RJ', '24': 'RJ',
    '31': 'MG', '32': 'MG', '41': 'PR', '42': 'SC', '43': 'RS', '47': 'SC', '48': 'SC',
    '51': 'RS', '61': 'DF', '62': 'GO', '71': 'BA', '81': 'PE', '91': 'PA'
}

# --- FUNÇÕES AUXILIARES ---
def limpar_valor_paranoico(valor):
    if pd.isna(valor): return ""
    s_val = str(valor).strip()
    if 'E' in s_val.upper(): # Notação científica
        try: s_val = '{:.0f}'.format(float(s_val))
        except: pass
    if s_val.endswith('.0'): s_val = s_val[:-2]
    return re.sub(r'\D', '', s_val)

def calcular_digito(cnpj_parcial):
    tamanho = len(cnpj_parcial)
    pesos = [5,4,3,2,9,8,7,6,5,4,3,2] if tamanho == 12 else [6,5,4,3,2,9,8,7,6,5,4,3,2]
    soma = sum(int(d) * pesos[i] for i, d in enumerate(cnpj_parcial))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)

def garantir_cnpj_matriz(cnpj_sujo):
    cnpj_limpo = limpar_valor_paranoico(cnpj_sujo)
    cnpj_limpo = cnpj_limpo.zfill(14)
    if len(cnpj_limpo) < 8: return ""
    raiz = cnpj_limpo[:8]
    cnpj_sem_dv = raiz + "0001"
    dv1 = calcular_digito(cnpj_sem_dv)
    dv2 = calcular_digito(cnpj_sem_dv + dv1)
    return cnpj_sem_dv + dv1 + dv2

# --- VIEWSET PRINCIPAL ---
class ParceiroViewSet(viewsets.ModelViewSet):
    queryset = Parceiro.objects.all().order_by('-score_atual')
    serializer_class = ParceiroSerializer

    # --- AÇÃO 1: IMPORTAR EXCEL (CARGA DE PARCEIROS) ---
    @action(detail=False, methods=['post'])
    def importar_excel(self, request):
        arquivo = request.FILES.get('file')
        if not arquivo:
            return Response({"erro": "Nenhum arquivo enviado."}, status=400)

        try:
            df = pd.read_excel(arquivo)
            df.columns = df.columns.str.strip().str.upper()
            
            criados = 0
            atualizados = 0

            # Mapeamento para garantir robustez
            MAPA_SERVICOS = {
                "PLANEJAMENTO DE PROJETOS": "Planejamento de Projetos/Incorporação",
                "ESTUDO DE VIABILIDADE": "Estudo de Viabilidade",
                "ORÇAMENTO": "Orçamento",
                "PLANEJAMENTO": "Planejamento",
                "MONITORAMENTO": "Monitoramento e Controle",
                "GERENCIAMENTO DE OBRA": "Gerenciamento de Obra",
                "CONSULTORIA": "Consultoria",
                "CURSOS": "Cursos",
                "BIM": "BIM",
                "MENTORIA": "Mentoria Lean",
                "GESTÃO DE PESSOAS": "Gestão de Pessoas",
                "PROJETOS COMPLE": "Projetos Complementares",
                "QUALIDADE": "Qualidade",
                "GERENCIAMENTO DE PROJETO": "Gerenciamento de Projeto/Contrato",
                "GERENCIAMENTO FISICO": "Gerenciamento Físico-Financeiro",
                "SUSTENTÁVEIS": "Soluções Sustentáveis"
            }

            for _, row in df.iterrows():
                try:
                    nome_empresa = str(row.get("EMPRESA", "")).strip()
                    if not nome_empresa or nome_empresa == "nan": continue

                    contato = str(row.get("CONTATO", "")).strip()
                    if contato == "nan": contato = str(row.get("CONTATOS", "")).strip()
                    if contato == "nan": contato = "Não informado"

                    email = str(row.get("E-MAIL", row.get("EMAIL", ""))).strip()
                    if email == "nan": email = ""

                    telefone = str(row.get("TELEFONE", row.get("CELULAR", ""))).strip()
                    if telefone == "nan": telefone = ""

                    area_atuacao = str(row.get("AREA DE ATUAÇÃO", row.get("AREA DE ATUACAO", row.get("ESTADO", "")))).strip()
                    if area_atuacao == "nan": area_atuacao = ""

                    cidade = str(row.get("CIDADE", row.get("ENDEREÇO", ""))).strip()
                    if cidade == "nan": cidade = ""

                    # Lógica de Serviços
                    servicos_raw = str(row.get("SERVIÇOS PRESTADOS", "")).upper()
                    servicos_finais = []
                    for chave, valor_correto in MAPA_SERVICOS.items():
                        if chave in servicos_raw:
                            servicos_finais.append(valor_correto)
                    servicos_str = ", ".join(servicos_finais)

                    obj, created = Parceiro.objects.update_or_create(
                        empresa=nome_empresa,
                        defaults={
                            "contato_nome": contato,
                            "email": email,
                            "telefone": telefone,
                            "estados_atuacao": area_atuacao,
                            "cidade": cidade,
                            "servicos": servicos_str
                        }
                    )
                    if created: criados += 1
                    else: atualizados += 1

                except Exception as loop_erro:
                    print(f"Pulei a linha {nome_empresa}: {loop_erro}")
                    continue

            return Response({"mensagem": f"Sucesso! {criados} novos parceiros, {atualizados} atualizados."})

        except Exception as e:
            return Response({"erro": str(e)}, status=500)

    # --- AÇÃO 2: REGISTRAR PONTOS ---
    @action(detail=True, methods=['post'])
    def registrar_indicacao(self, request, pk=None):
        parceiro = self.get_object()
        try:
            pontos_str = request.data.get('pontos')
            tipo = request.data.get('tipo', 'Indicação')
            
            if not pontos_str:
                return Response({"erro": "Pontos não informados"}, status=400)

            pontos_decimal = Decimal(str(pontos_str))

            HistoricoPontuacao.objects.create(
                parceiro=parceiro,
                tipo=tipo,
                pontos=pontos_decimal,
                descricao="Lançamento via Painel"
            )

            parceiro.score_atual += pontos_decimal
            parceiro.ultima_indicacao = timezone.now().date()
            parceiro.save()

            serializer = self.get_serializer(parceiro)
            return Response(serializer.data)

        except Exception as e:
            return Response({"erro": str(e)}, status=500)

    # --- AÇÃO 3: AGENTE DE LEADS 12.0 (VERSÃO COMPLETA) ---
    @action(detail=False, methods=['post'])
    def qualificar_leads(self, request):
        file_leads = request.FILES.get('file')
        file_clientes = request.FILES.get('file_clientes') 

        if not file_leads: return Response({"erro": "Arquivo de leads não enviado"}, status=400)

        # 1. CARREGA PIPEDRIVE (Histórico Completo)
        print("--- Consultando Pipedrive ---")
        # Nota: Certifique-se que services.py está atualizado para retornar Data e Tipo
        crm_por_cnpj, crm_por_nome = buscar_dados_pipedrive(TOKEN_PIPEDRIVE)
        
        # 2. CARREGA ECOSSISTEMA (PLANILHA NOVA)
        dados_ecossistema = {} 
        if file_clientes:
            try:
                # Lê considerando cabeçalho na primeira linha
                df_cli = pd.read_excel(file_clientes)
                df_cli.columns = df_cli.columns.str.strip()
                col_cnpj = df_cli.columns[0] # Assume CNPJ na 1ª coluna
                
                for _, row in df_cli.iterrows():
                    raw_cnpj = str(row[col_cnpj])
                    numeros = limpar_valor_paranoico(raw_cnpj)
                    if 8 <= len(numeros) <= 14:
                        raiz = numeros.zfill(14)[:8]
                        dados_cliente = {
                            'Sienge': row.get('Sienge', ''),
                            'Prevision': row.get('Prevision', ''),
                            'CV': row.get('CV', ''),
                            'Construpoint': row.get('Construpoint', ''),
                            'MRR Sienge': row.get('MRR Sienge', ''),
                            'MRR Prevision': row.get('MRR Prevision', ''),
                            'MRR CV CRM': row.get('MRR CV CRM', '')
                        }
                        dados_ecossistema[raiz] = dados_cliente
                print(f"Base Ecossistema carregada: {len(dados_ecossistema)} registros.")
            except Exception as e: print(f"Erro ao ler Base Ecossistema: {e}")

        # 3. LEADS (ARQUIVO DE ENTRADA)
        try: df = pd.read_excel(file_leads)
        except: return Response({"erro": "Arquivo inválido"}, status=400)
        
        if len(df.columns) < 5: return Response({"erro": "Colunas insuficientes. Use o modelo padrão."}, status=400)

        coluna_empresa = df.columns[4] 
        coluna_telefone = df.columns[2]
        
        headers_serper = {'X-API-KEY': API_KEY_SERPER, 'Content-Type': 'application/json'}
        url_search = "https://google.serper.dev/search"

        for index, row in df.iterrows():
            empresa_nome = str(row[coluna_empresa]).strip()
            telefone_bruto = str(row[coluna_telefone])
            
            # --- BUSCA GOOGLE (ENRIQUECIMENTO) ---
            cnpj_matriz_final = ""
            ddd_lead = ''.join(filter(str.isdigit, telefone_bruto))[:2]
            estado_lead = DDD_ESTADOS.get(ddd_lead, "")

            try:
                termo = f"{empresa_nome} CNPJ"
                if estado_lead: termo += f" {estado_lead}"
                
                payload = json.dumps({"q": termo, "num": 5})
                response = requests.post(url_search, headers=headers_serper, data=payload)
                results = response.json().get("organic", [])
                
                candidatos = []
                for res in results:
                    texto = (res.get("title", "") + " " + res.get("snippet", "")).upper()
                    achados = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
                    for c_achado in achados:
                        c_convertido = garantir_cnpj_matriz(c_achado)
                        score = 0
                        if "CONSTRU" in texto or "ENGENHARIA" in texto: score += 2
                        if estado_lead and estado_lead in texto: score += 5
                        candidatos.append({'cnpj': c_convertido, 'score': score})

                if candidatos:
                    candidatos.sort(key=lambda x: x['score'], reverse=True)
                    cnpj_matriz_final = candidatos[0]['cnpj']
            except: pass

            # --- BRASIL API ---
            atividade = "Não verificada"
            if cnpj_matriz_final:
                try:
                    url_brasil = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_matriz_final}"
                    resp = requests.get(url_brasil, timeout=5)
                    if resp.status_code == 200:
                        dados = resp.json()
                        atividade = dados.get('cnae_fiscal_descricao', 'Não informado')
                    else: atividade = "CNPJ não encontrado na Base"
                except: pass

            # --- INTELIGÊNCIA PIPEDRIVE (CRUZAMENTO) ---
            status_crm = "Disponível"
            contato_crm = ""
            links_crm = ""
            
            hist_erp = set()
            hist_produto = set()
            hist_tipologia = set()
            
            data_ultimo_card = ""
            tipo_empresa_ultimo = ""
            link_ultimo_card = ""

            # 1. Match por CNPJ
            matches = []
            if cnpj_matriz_final and cnpj_matriz_final in crm_por_cnpj:
                matches = crm_por_cnpj[cnpj_matriz_final]
                status_crm = "ENCONTRADO (CNPJ)"
            
            # 2. Match por Nome (Fallback)
            elif status_crm == "Disponível" and empresa_nome.lower() in crm_por_nome:
                matches = crm_por_nome[empresa_nome.lower()]
                status_crm = "ENCONTRADO (Nome)"

            if matches:
                # Ordena do mais recente para o mais antigo
                # Garante que o campo data_criacao exista (veja services.py)
                matches.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
                
                mais_recente = matches[0]
                data_raw = mais_recente.get('data_criacao', '')
                data_ultimo_card = data_raw[:10] if data_raw else ""
                tipo_empresa_ultimo = mais_recente.get('tipo_empresa', '')
                link_ultimo_card = mais_recente.get('link', '')

                # Verifica se TEM ABERTO
                tem_aberto = any(m.get('status') == 'open' for m in matches)
                if tem_aberto:
                    status_crm = "EM ABERTO (Não Prospectar)"
                else:
                    status_crm = f"JÁ NEGOCIADO (Último: {data_ultimo_card})"

                contato_crm = ", ".join({m['contato'] for m in matches if m['contato'] != "Sem Contato"})
                links_crm = " | ".join([m['link'] for m in matches])
                
                # Acumula inteligência
                for m in matches:
                    if m.get('erp'): hist_erp.add(m['erp'])
                    if m.get('produto'): hist_produto.add(m['produto'])
                    if m.get('tipologia'): hist_tipologia.add(m['tipologia'])

            # --- DADOS ECOSSISTEMA ---
            eco_sienge = ""
            eco_prevision = ""
            eco_cv = ""
            eco_mrr_sienge = ""
            eco_mrr_prevision = ""
            
            if cnpj_matriz_final:
                raiz_cnpj = cnpj_matriz_final[:8]
                if raiz_cnpj in dados_ecossistema:
                    info_eco = dados_ecossistema[raiz_cnpj]
                    eco_sienge = info_eco.get('Sienge', '')
                    eco_prevision = info_eco.get('Prevision', '')
                    eco_cv = info_eco.get('CV', '')
                    eco_mrr_sienge = info_eco.get('MRR Sienge', '')
                    eco_mrr_prevision = info_eco.get('MRR Prevision', '')

            # --- SITE e TIPOLOGIA WEB ---
            site_final = "Não encontrado"
            try:
                p_site = json.dumps({"q": f"{empresa_nome} site oficial", "num": 1})
                r_site = requests.post(url_search, headers=headers_serper, data=p_site)
                if r_site.json().get("organic"): site_final = r_site.json().get("organic")[0].get("link")
            except: pass

            tipologia_site = "nao_identificado"
            txt = (empresa_nome + " " + site_final + " " + atividade).lower()
            if any(x in txt for x in ['lote', 'bairro', 'urbanismo']): tipologia_site = "loteamento"
            elif any(x in txt for x in ['edific', 'residencial', 'incorp']): tipologia_site = "vertical"
            elif any(x in txt for x in ['industria', 'galpao']): tipologia_site = "industrial"

            # --- PREENCHIMENTO EXCEL FINAL ---
            df.at[index, 'CNPJ Encontrado'] = cnpj_matriz_final
            df.at[index, 'Atividade Principal'] = atividade
            df.at[index, 'Site'] = site_final
            
            # CRM Inteligente
            df.at[index, 'Status CRM'] = status_crm
            df.at[index, 'Data Último Card'] = data_ultimo_card
            df.at[index, 'Tipo Empresa (CRM)'] = tipo_empresa_ultimo
            df.at[index, 'Link Último Card'] = link_ultimo_card
            
            df.at[index, 'Contato CRM'] = contato_crm
            df.at[index, 'Histórico ERP'] = ", ".join(hist_erp)
            df.at[index, 'Histórico Produtos'] = ", ".join(hist_produto)
            
            # Ecossistema
            df.at[index, 'Status Sienge'] = eco_sienge
            df.at[index, 'MRR Sienge'] = eco_mrr_sienge
            df.at[index, 'Status Prevision'] = eco_prevision
            df.at[index, 'MRR Prevision'] = eco_mrr_prevision
            
            df.at[index, 'Tipologia (Web)'] = tipologia_site

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=leads_super_qualificados.xlsx'
        df.to_excel(response, index=False)
        return response
