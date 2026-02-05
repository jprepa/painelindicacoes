import requests

def buscar_dados_pipedrive(api_token):
    """
    Retorna dicionários com LISTAS de negócios, incluindo o LINK direto para o card.
    Ex: {'1234...': [{'contato': 'João', 'link': 'https://.../deal/10'}]}
    """
    # 1. Primeiro, descobre o seu domínio (ex: 'prevision.pipedrive.com')
    try:
        resp_user = requests.get("https://api.pipedrive.com/v1/users/me", params={'api_token': api_token})
        domain = resp_user.json().get('data', {}).get('company_domain', 'app')
    except:
        domain = 'app' # Fallback se falhar
    
    url_deals = "https://api.pipedrive.com/v1/deals"
    
    # --- SEU HASH DO CAMPO CNPJ (Confira se é este mesmo!) ---
    CAMPO_CNPJ_HASH = '39fa8d7e6f5c4b3a21908...' 
    # ---------------------------------------------------------

    dados_por_cnpj = {}
    dados_por_nome = {}
    
    start = 0
    limit = 500 

    while True:
        params = {
            'api_token': api_token,
            'status': 'open',
            'start': start,
            'limit': limit,
        }

        try:
            response = requests.get(url_deals, params=params, timeout=10)
            data = response.json().get('data')
            if not data: break 

            for deal in data:
                # Dados básicos
                deal_id = deal.get('id')
                # MONTA O LINK DO CARD
                link_card = f"https://{domain}.pipedrive.com/deal/{deal_id}"
                
                nome_org = "Sem Nome"
                if deal.get('org_id'): nome_org = deal['org_id'].get('name', 'Sem Nome')
                
                nome_pessoa = "Sem Contato"
                if deal.get('person_id'): nome_pessoa = deal['person_id'].get('name', 'Sem Contato')

                # Pacote com Link
                info = {
                    'id': deal_id,
                    'nome_crm': nome_org,
                    'contato': nome_pessoa,
                    'link': link_card
                }

                # --- Lógica de Lista (Append) para CNPJ ---
                cnpj_raw = deal.get(CAMPO_CNPJ_HASH)
                if cnpj_raw:
                    c_limpo = str(cnpj_raw).replace('.', '').replace('/', '').replace('-', '').strip()
                    if c_limpo:
                        if c_limpo not in dados_por_cnpj: dados_por_cnpj[c_limpo] = []
                        dados_por_cnpj[c_limpo].append(info)

                # --- Lógica de Lista (Append) para Nome ---
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
