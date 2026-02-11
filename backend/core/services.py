import requests
from datetime import datetime

# --- DICIONÁRIO DE TRADUÇÃO (PREENCHIDO COM SEUS DADOS) ---
MAPA_IDS_PIPEDRIVE = {
    # --- PRODUTOS SUGERIDOS ---
    '1395': 'Prevision PI',
    '1396': 'Prevision Obra Lean',
    '1397': 'Prevision Obra Gantt',
    '1435': 'Prevision Gantt Start',
    '1436': 'Prevision Gantt Pro/Premium',
    '1437': 'Prevision LOB Pro/Premium',
    '1438': 'Prevision Planejamento de Incorporação',

    # --- ERP ---
    '1254': '90TI - Compor e Gestor 90',
    '1252': 'Conta Azul',
    '1251': 'Excel',
    '303':  'Informakon',
    '1261': 'Koper',
    '1260': 'Mais Controle',
    '34':   'Mega',
    '289':  'Obra Prima',
    '1253': 'Omie',
    '1256': 'Orçafascio',
    '36':   'SAP',
    '1255': 'Server Obras',
    '33':   'Siecon',
    '1258': 'Sienge Go',
    '1259': 'Sienge Plataforma',
    '287':  'Strato',
    '387':  'Supera',
    '35':   'TOTVS',
    '37':   'UAU',
    '1257': 'Versato (Volare)',
    '1262': 'Não Informado',
    '38':   'Não utiliza',
    '39':   'Outros',

    # --- TIPOLOGIA DE OBRA ---
    '41':   'Edifícios verticais',
    '44':   'Comerciais/Corporativas',
    '45':   'Industrial',
    '47':   'Loteamentos',
    '573':  'Casas',
    '1238': 'Pública civil',
    '1239': 'Pública de infraestrutura',
    '1240': 'Reforma',
    '1241': 'Residencial',
    '1242': 'Obras Horizontais',
    '1243': 'Prestação de Serviços',
    '1244': 'MCMV',
    '1245': 'Condomínios de casas',
    '1246': 'Galpões',
    '48':   'Outros',

    # --- TIPO DE EMPRESA ---
    '49': 'Construtora',
    '50': 'Incorporadora',
    '51': 'Consultoria',
    '52': 'Administradora (SPE)',
    '53': 'Empreiteira',
    '54': 'Reformas',
    '55': 'Varejo'
}

def traduzir_id(valor_bruto):
    """Converte ID numérico (ex: 1262) para Texto (ex: Sienge)"""
    if not valor_bruto: return ""
    
    # Se for uma lista de IDs (ex: "1436, 1438") vindo do Pipedrive
    if "," in str(valor_bruto):
        partes = [p.strip() for p in str(valor_bruto).split(",")]
        nomes = [MAPA_IDS_PIPEDRIVE.get(p, p) for p in partes] # Se não achar, mantém o número
        return ", ".join(nomes)
        
    # Se for um valor único
    return MAPA_IDS_PIPEDRIVE.get(str(valor_bruto), str(valor_bruto))

def buscar_dados_pipedrive(api_token):
    try:
        resp_user = requests.get("https://api.pipedrive.com/v1/users/me", params={'api_token': api_token})
        domain = resp_user.json().get('data', {}).get('company_domain', 'app')
    except:
        domain = 'app'
    
    url_deals = "https://api.pipedrive.com/v1/deals"
    
    # --- HASHES (CÓDIGOS DOS CAMPOS) - JÁ PREENCHIDOS DAS SUAS IMAGENS ---
    # Só o CNPJ que mantive o do seu código anterior pois não apareceu nas imagens novas
    CAMPO_CNPJ_HASH = '39fa8d7e6f5c4b3a21908...' # <--- CONFIRA SE ESTE É O DO CNPJ MESMO!
    
    CAMPO_ERP_HASH = '4691b401ffd1480fe76ea54ebfc0c6358bb42afb'
    CAMPO_PRODUTO_HASH = 'f01c7923ea23a7a30659792ffd5f38f3773e455a'
    CAMPO_TIPOLOGIA_HASH = '04ca3f3994424d148ae157aa38a0ed051abc0c09'
    CAMPO_TIPO_EMPRESA_HASH = '287046cd13f6a3a9783649dc2ebfc521307b8c77'
    # ---------------------------------------------------------------------

    dados_por_cnpj = {}
    dados_por_nome = {}
    
    start = 0
    limit = 500 

    while True:
        # Busca TUDO (status='all_not_deleted') para ver histórico antigo e aberto
        params = {
            'api_token': api_token,
            'status': 'all_not_deleted', 
            'start': start,
            'limit': limit,
        }

        try:
            response = requests.get(url_deals, params=params, timeout=10)
            data = response.json().get('data')
            if not data: break 

            for deal in data:
                deal_id = deal.get('id')
                # Data de criação do card (para saber se é recente)
                data_criacao = deal.get('add_time', '') 
                
                link_card = f"https://{domain}.pipedrive.com/deal/{deal_id}"
                
                nome_org = "Sem Nome"
                if deal.get('org_id'): nome_org = deal['org_id'].get('name', 'Sem Nome')
                
                nome_pessoa = "Sem Contato"
                if deal.get('person_id'): nome_pessoa = deal['person_id'].get('name', 'Sem Contato')

                # --- Captura E TRADUZ os Campos ---
                erp_valor = traduzir_id(deal.get(CAMPO_ERP_HASH))
                produto_valor = traduzir_id(deal.get(CAMPO_PRODUTO_HASH))
                tipologia_valor = traduzir_id(deal.get(CAMPO_TIPOLOGIA_HASH))
                tipo_empresa_valor = traduzir_id(deal.get(CAMPO_TIPO_EMPRESA_HASH))

                info = {
                    'id': deal_id,
                    'status': deal.get('status'), # 'open', 'won', 'lost'
                    'data_criacao': data_criacao,
                    'nome_crm': nome_org,
                    'contato': nome_pessoa,
                    'link': link_card,
                    'erp': erp_valor,
                    'produto': produto_valor,
                    'tipologia': tipologia_valor,
                    'tipo_empresa': tipo_empresa_valor
                }

                # --- Lógica de Lista (CNPJ) ---
                cnpj_raw = deal.get(CAMPO_CNPJ_HASH)
                if cnpj_raw:
                    c_limpo = str(cnpj_raw).replace('.', '').replace('/', '').replace('-', '').strip()
                    if c_limpo:
                        if c_limpo not in dados_por_cnpj: dados_por_cnpj[c_limpo] = []
                        dados_por_cnpj[c_limpo].append(info)

                # --- Lógica de Lista (Nome) ---
                n_limpo = nome_org.lower().strip()
                if n_limpo:
                    if n_limpo not in dados_por_nome: dados_por_nome[n_limpo] = []
                    dados_por_nome[n_limpo].append(info)

            start += limit
            if len(data) < limit: break
                
        except Exception as e:
            print(f"Erro Pipedrive: {e}")
            break
            
    return dados_por_cnpj, dados_por_nome
