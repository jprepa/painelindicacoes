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
# IMPORTAÇÃO CORRIGIDA (Isso resolve o erro do log)
from .services import consultar_pipedrive_pontual 

# --- CONFIGURAÇÕES ---
TOKEN_PIPEDRIVE = "952556ce51a1938462a38091c1ea9dfb38b8351c"
API_KEY_SERPER = "2256b3e6069092a66862efd5bdd6f7d55f211a1a"

DDD_ESTADOS = {
    '11': 'SP', '12': 'SP', '13': 'SP', '19': 'SP', '21': 'RJ', '22': 'RJ', '24': 'RJ',
    '31': 'MG', '32': 'MG', '41': 'PR', '42': 'SC', '43': 'RS', '47': 'SC', '48': 'SC',
    '51': 'RS', '61': 'DF', '62': 'GO', '71': 'BA', '81': 'PE', '91': 'PA'
}

# --- FUNÇÕES AUXILIARES ---
def limpar_valor_paranoico(valor):
    if pd.isna(valor): return ""
    s_val = str(valor).strip()
    if 'E' in s_val.upper(): 
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

class ParceiroViewSet(viewsets.ModelViewSet):
    queryset = Parceiro.objects.all().order_by('-score_atual')
    serializer_class = ParceiroSerializer

    @action(detail=False, methods=['post'])
    def importar_excel(self, request):
        arquivo = request.FILES.get('file')
        if not arquivo: return Response({"erro": "Nenhum arquivo enviado."}, status=400)
        try:
            df = pd.read_excel(arquivo)
            df.columns = df.columns.str.strip().str.upper()
            criados = 0
            atualizados = 0
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
                    servicos_raw = str(row.get("SERVIÇOS PRESTADOS", "")).upper()
                    servicos_finais = []
                    for chave, valor_correto in MAPA_SERVICOS.items():
                        if chave in servicos_raw: servicos_finais.append(valor_correto)
                    servicos_str = ", ".join(servicos_finais)
                    obj, created = Parceiro.objects.update_or_create(
                        empresa=nome_empresa,
                        defaults={ "contato_nome": contato, "email": email, "telefone": telefone, "estados_atuacao": area_atuacao, "cidade": cidade, "servicos": servicos_str }
                    )
                    if created: criados += 1
                    else: atualizados += 1
                except: continue
            return Response({"mensagem": f"Sucesso! {criados} novos, {atualizados} atualizados."})
        except Exception as e: return Response({"erro": str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def registrar_indicacao(self, request, pk=None):
        parceiro = self.get_object()
        try:
            pontos_str = request.data.get('pontos')
            tipo = request.data.get('tipo', 'Indicação')
            if not pontos_str: return Response({"erro": "Pontos não informados"}, status=400)
            pontos_decimal = Decimal(str(pontos_str))
            HistoricoPontuacao.objects.create(parceiro=parceiro, tipo=tipo, pontos=pontos_decimal, descricao="Lançamento via Painel")
            parceiro.score_atual += pontos_decimal
            parceiro.ultima_indicacao = timezone.now().date()
            parceiro.save()
            return Response(self.get_serializer(parceiro).data)
        except Exception as e: return Response({"erro": str(e)}, status=500)

    # --- AGENTE DE LEADS 18.0 (LEVE, SNIPER E COM FÓRMULAS) ---
    @action(detail=False, methods=['post'])
    def qualificar_leads(self, request):
        file_leads = request.FILES.get('file')
        if not file_leads: return Response({"erro": "Arquivo de leads não enviado"}, status=400)

        # 1. LEITURA DOS LEADS
        try: df = pd.read_excel(file_leads)
        except: return Response({"erro": "Arquivo inválido"}, status=400)
        
        if len(df.columns) < 5: return Response({"erro": "Colunas insuficientes."}, status=400)

        coluna_empresa = df.columns[4] 
        coluna_telefone = df.columns[2]
        
        headers_serper = {'X-API-KEY': API_KEY_SERPER, 'Content-Type': 'application/json'}
        url_search = "https://google.serper.dev/search"

        output_rows = []

        # 2. LOOP LINHA A LINHA (PROCESSAMENTO ISOLADO)
        for index, row in df.iterrows():
            empresa_nome = str(row[coluna_empresa]).strip()
            telefone_bruto = str(row[coluna_telefone])
            
            # --- A. BUSCA GOOGLE ---
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

            # --- B. BRASIL API ---
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

            # --- C. PIPEDRIVE (MODO SNIPER) ---
            # Chama a função nova, passando apenas o CNPJ/Nome desta linha
            dados_pipe = consultar_pipedrive_pontual(TOKEN_PIPEDRIVE, cnpj_matriz_final, empresa_nome)
            
            status_crm, data_card, tipo_emp = "Disponível", "", ""
            link_card, contato_crm, hist_erp, hist_prod = "", "", "", ""

            if dados_pipe:
                status_crm = dados_pipe['status_crm']
                data_card = dados_pipe['data_ultimo']
                tipo_emp = dados_pipe['tipo_empresa']
                link_card = dados_pipe['link_ultimo']
                contato_crm = dados_pipe['contato_crm']
                hist_erp = dados_pipe['hist_erp']
                hist_prod = dados_pipe['hist_prod']

            # --- D. SITE WEB ---
            site_final, tipologia_site = "Não encontrado", "nao_identificado"
            try:
                p_site = json.dumps({"q": f"{empresa_nome} site oficial", "num": 1})
                r_site = requests.post(url_search, headers=headers_serper, data=p_site)
                if r_site.json().get("organic"): site_final = r_site.json().get("organic")[0].get("link")
            except: pass

            txt = (empresa_nome + " " + site_final + " " + atividade).lower()
            if any(x in txt for x in ['lote', 'bairro', 'urbanismo']): tipologia_site = "loteamento"
            elif any(x in txt for x in ['edific', 'residencial', 'incorp']): tipologia_site = "vertical"
            elif any(x in txt for x in ['industria', 'galpao']): tipologia_site = "industrial"

            # --- PREPARA A LINHA DO EXCEL (COM FÓRMULAS) ---
            row_excel = index + 2 
            def gerar_vlookup(col_index):
                return f"=IFERROR(VLOOKUP(F{row_excel}, 'Base Ecossistema'!A:P, {col_index}, FALSE), \"\")"

            output_rows.append({
                'Email': row.get(df.columns[0]), 
                'Nome': row.get(df.columns[1]),
                'Telefone': row.get(df.columns[2]),
                'Cargo': row.get(df.columns[3]),
                'Empresa': empresa_nome,
                'CNPJ Encontrado': cnpj_matriz_final,
                'Atividade': atividade,
                'Site': site_final,
                'Status CRM': status_crm,
                'Data Card': data_card,
                'Tipo Emp': tipo_emp,
                'Link Card': link_card,
                'Contato CRM': contato_crm,
                'Hist. ERP': hist_erp,
                'Hist. Prod': hist_prod,
                'Tipologia': tipologia_site,
                # Fórmulas
                'Porte': gerar_vlookup(2),
                'Status Sienge': gerar_vlookup(3),
                'S. Construcompras': gerar_vlookup(4),
                'S. Construmanager': gerar_vlookup(5),
                'S. Construpoint': gerar_vlookup(6),
                'Status CV': gerar_vlookup(7),
                'Status Prevision': gerar_vlookup(8),
                'Status GO': gerar_vlookup(9),
                'MRR Sienge': gerar_vlookup(10),
                'MRR Constrcomp': gerar_vlookup(11),
                'MRR Constrmanag': gerar_vlookup(12),
                'MRR Constrpoint': gerar_vlookup(13),
                'MRR CV': gerar_vlookup(14),
                'MRR Prevision': gerar_vlookup(15),
                'MRR GO': gerar_vlookup(16)
            })

        # --- EXPORTAÇÃO ---
        df_final = pd.DataFrame(output_rows)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=leads_inteligentes_v18.xlsx'
        
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, sheet_name='Leads Qualificados', index=False)
            workbook = writer.book
            worksheet_base = workbook.add_worksheet('Base Ecossistema')
            worksheet_base.write('A1', 'COLE AQUI A BASE DO ECOSSISTEMA (Coluna A deve ser o CNPJ)')
            
        return response
