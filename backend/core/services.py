import requests

def buscar_cnpjs_pipedrive(api_token):
    """
    Busca todos os negócios em aberto no Pipedrive e retorna
    uma lista de CNPJs limpos para verificação rápida.
    """
    # URL da API de Deals (Negócios)
    url = "https://api.pipedrive.com/v1/deals"
    
    # --- PREENCHA AQUI ---
    # O hash do campo personalizado onde você guarda o CNPJ no Pipedrive
    CAMPO_CNPJ_HASH = '18e8111634bc53a7bb1cee2f27638df164a4dff0' 
    # ---------------------

    cnpjs_em_aberto = set()
    start = 0
    limit = 500 

    while True:
        params = {
            'api_token': api_token,
            'status': 'open', # Só pega o que está em aberto
            'start': start,
            'limit': limit,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status() # Avisa se der erro 400/500
            
            data = response.json().get('data')
            
            if not data:
                break 

            for deal in data:
                # Pega o valor usando o código do campo
                cnpj = deal.get(CAMPO_CNPJ_HASH)
                
                if cnpj:
                    # Limpa pontos e traços para comparar fácil depois
                    cnpj_limpo = str(cnpj).replace('.', '').replace('/', '').replace('-', '').strip()
                    cnpjs_em_aberto.add(cnpj_limpo)

            start += limit
            if len(data) < limit:
                break
                
        except Exception as e:
            print(f"Erro ao conectar no Pipedrive: {e}")
            break
            
    return cnpjs_em_aberto
