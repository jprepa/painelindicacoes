import requests
from datetime import datetime

def buscar_dados_pipedrive(api_token):
    """
    Retorna dicionários com dados do CRM, incluindo Data, Tipo de Empresa e Status.
    """
    try:
        resp_user = requests.get("https://api.pipedrive.com/v1/users/me", params={'api_token': api_token})
        domain = resp_user.json().get('data', {}).get('company_domain', 'app')
    except:
        domain = 'app'
    
    url_deals = "https://api.pipedrive.com/v1/deals"
    
    # --- PREENCHA COM SEUS CÓDIGOS (HASHES) ---
    CAMPO_CNPJ_HASH = '18e8111634bc53a7bb1cee2f27638df164a4dff0' # <--- Seu Hash de CNPJ
    
    CAMPO_ERP_HASH = '4691b401ffd1480fe76ea54ebfc0c6358bb42afb'
    CAMPO_PRODUTO_HASH = 'f01c7923ea23a7a30659792ffd5f38f3773e455a'
    CAMPO_TIPOLOGIA_HASH = '04ca3f3994424d148ae157aa38a0ed051abc0c09'
    CAMPO_TIPO_EMPRESA_HASH = '287046cd13f6a3a9783649dc2ebfc521307b8c77' # <--- NOVO!
    # ------------------------------------------

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

                # --- Captura os Campos Personalizados ---
                erp_valor = deal.get(CAMPO_ERP_HASH) or ""
                produto_valor = deal.get(CAMPO_PRODUTO_HASH) or ""
                tipologia_valor = deal.get(CAMPO_TIPOLOGIA_HASH) or ""
                tipo_empresa_valor = deal.get(CAMPO_TIPO_EMPRESA_HASH) or "" # <--- NOVO

                info = {
                    'id': deal_id,
                    'status': deal.get('status'), # 'open', 'won', 'lost'
                    'data_criacao': data_criacao,
                    'nome_crm': nome_org,
                    'contato': nome_pessoa,
                    'link': link_card,
                    'erp': str(erp_valor),
                    'produto': str(produto_valor),
                    'tipologia': str(tipologia_valor),
                    'tipo_empresa': str(tipo_empresa_valor) # <--- NOVO
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
