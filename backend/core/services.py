import requests
from datetime import datetime

# --- SEU MAPA DE TRADUÇÃO (MANTIDO) ---
MAPA_IDS_PIPEDRIVE = {
    # PRODUTOS
    '1395': 'Prevision PI', '1396': 'Prevision Obra Lean', '1397': 'Prevision Obra Gantt',
    '1435': 'Prevision Gantt Start', '1436': 'Prevision Gantt Pro/Premium',
    '1437': 'Prevision LOB Pro/Premium', '1438': 'Prevision Planejamento de Incorporação',
    # ERP
    '1254': '90TI - Compor e Gestor 90', '1252': 'Conta Azul', '1251': 'Excel',
    '303': 'Informakon', '1261': 'Koper', '1260': 'Mais Controle', '34': 'Mega',
    '289': 'Obra Prima', '1253': 'Omie', '1256': 'Orçafascio', '36': 'SAP',
    '1255': 'Server Obras', '33': 'Siecon', '1258': 'Sienge Go', '1259': 'Sienge Plataforma',
    '287': 'Strato', '387': 'Supera', '35': 'TOTVS', '37': 'UAU',
    '1257': 'Versato (Volare)', '1262': 'Não Informado', '38': 'Não utiliza', '39': 'Outros',
    # TIPOLOGIA
    '41': 'Edifícios verticais', '44': 'Comerciais/Corporativas', '45': 'Industrial',
    '47': 'Loteamentos', '573': 'Casas', '1238': 'Pública civil',
    '1239': 'Pública de infraestrutura', '1240': 'Reforma', '1241': 'Residencial',
    '1242': 'Obras Horizontais', '1243': 'Prestação de Serviços', '1244': 'MCMV',
    '1245': 'Condomínios de casas', '1246': 'Galpões', '48': 'Outros',
    # TIPO EMPRESA
    '49': 'Construtora', '50': 'Incorporadora', '51': 'Consultoria',
    '52': 'Administradora (SPE)', '53': 'Empreiteira', '54': 'Reformas', '55': 'Varejo'
}

def traduzir_id(valor_bruto):
    if not valor_bruto: return ""
    if "," in str(valor_bruto):
        partes = [p.strip() for p in str(valor_bruto).split(",")]
        nomes = [MAPA_IDS_PIPEDRIVE.get(p, p) for p in partes]
        return ", ".join(nomes)
    return MAPA_IDS_PIPEDRIVE.get(str(valor_bruto), str(valor_bruto))

def consultar_pipedrive_pontual(api_token, cnpj_busca, nome_busca):
    """
    Busca cirúrgica no Pipedrive por um termo específico (CNPJ ou Nome).
    Retorna o histórico consolidado e dados do último card.
    """
    
    # HASHES
    CAMPO_CNPJ_HASH = '39fa8d7e6f5c4b3a2190846067756f642468305c' 
    CAMPO_ERP_HASH = '4691b401ffd1480fe76ea54ebfc0c6358bb42afb'
    CAMPO_PRODUTO_HASH = 'f01c7923ea23a7a30659792ffd5f38f3773e455a'
    CAMPO_TIPOLOGIA_HASH = '04ca3f3994424d148ae157aa38a0ed051abc0c09'
    CAMPO_TIPO_EMPRESA_HASH = '287046cd13f6a3a9783649dc2ebfc521307b8c77'

    try:
        resp_user = requests.get("https://api.pipedrive.com/v1/users/me", params={'api_token': api_token})
        domain = resp_user.json().get('data', {}).get('company_domain', 'app')
    except:
        domain = 'app'

    # Função interna para fazer a busca na API
    def buscar_na_api(termo):
        if not termo or len(termo) < 3: return []
        url_search = "https://api.pipedrive.com/v1/deals/search"
        params = {'term': termo, 'api_token': api_token, 'limit': 5} # Traz até 5 matches
        try:
            r = requests.get(url_search, params=params, timeout=5)
            data = r.json().get('data', {}).get('items', [])
            return [i['item'] for i in data if i['item']['type'] == 'deal']
        except: return []

    # 1. Busca por CNPJ (Prioridade)
    deals_raw = buscar_na_api(cnpj_busca)
    
    # 2. Se não achou por CNPJ, tenta pelo Nome
    if not deals_raw and nome_busca:
        deals_raw = buscar_na_api(nome_busca)

    if not deals_raw:
        return None

    # 3. Processa os resultados (Busca detalhe de cada Deal)
    historico_matches = []
    
    for item in deals_raw:
        deal_id = item['id']
        try:
            r_detalhe = requests.get(f"https://api.pipedrive.com/v1/deals/{deal_id}", params={'api_token': api_token})
            deal = r_detalhe.json().get('data')
            if not deal: continue

            nome_org = deal.get('org_id', {}).get('name', 'Sem Nome') if deal.get('org_id') else 'Sem Nome'
            nome_pessoa = deal.get('person_id', {}).get('name', 'Sem Contato') if deal.get('person_id') else 'Sem Contato'
            
            info = {
                'id': deal_id,
                'status': deal.get('status'),
                'data_criacao': deal.get('add_time', ''),
                'nome_crm': nome_org,
                'contato': nome_pessoa,
                'link': f"https://{domain}.pipedrive.com/deal/{deal_id}",
                'erp': traduzir_id(deal.get(CAMPO_ERP_HASH)),
                'produto': traduzir_id(deal.get(CAMPO_PRODUTO_HASH)),
                'tipologia': traduzir_id(deal.get(CAMPO_TIPOLOGIA_HASH)),
                'tipo_empresa': traduzir_id(deal.get(CAMPO_TIPO_EMPRESA_HASH))
            }
            historico_matches.append(info)
        except: continue

    if not historico_matches: return None

    # 4. Consolida os dados
    historico_matches.sort(key=lambda x: x.get('data_criacao', ''), reverse=True)
    mais_recente = historico_matches[0]

    tem_aberto = any(m['status'] == 'open' for m in historico_matches)
    status_final = "EM ABERTO (Não Prospectar)" if tem_aberto else f"JÁ NEGOCIADO (Último: {mais_recente['data_criacao'][:10]})"

    erp_set = {m['erp'] for m in historico_matches if m['erp']}
    prod_set = {m['produto'] for m in historico_matches if m['produto']}
    contato_set = {m['contato'] for m in historico_matches if m['contato'] != "Sem Contato"}

    return {
        'status_crm': status_final,
        'data_ultimo': mais_recente['data_criacao'][:10],
        'tipo_empresa': mais_recente['tipo_empresa'],
        'link_ultimo': mais_recente['link'],
        'contato_crm': ", ".join(contato_set),
        'hist_erp': ", ".join(erp_set),
        'hist_prod': ", ".join(prod_set),
        'match_type': "ENCONTRADO"
    }
