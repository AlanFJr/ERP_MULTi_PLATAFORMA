import hmac
import hashlib
import time
import requests
import json
import config  # Nossas configurações

class ShopeeClient:
    def __init__(self):
        # Carrega dados do config.py
        self.partner_id = config.SHOPEE_PARTNER_ID
        self.partner_key = config.SHOPEE_PARTNER_KEY
        self.shop_id = config.SHOPEE_SHOP_ID
        self.host = config.SHOPEE_URL

    def _generate_signature(self, path, timestamp, access_token=None):
        """
        Cria a assinatura HMAC-SHA256 obrigatória.
        Fórmula V2: hmac(partner_id + path + timestamp + [access_token] + [shop_id], partner_key)
        """
        # Converte tudo para string antes de concatenar
        base_string = f"{self.partner_id}{path}{timestamp}"
        
        # Se tiver access_token (necessário para operações na loja), adiciona
        if access_token:
            base_string += access_token
        
        # Adiciona o shop_id
        base_string += str(self.shop_id)

        # Gera o Hash usando a chave secreta
        signature = hmac.new(
            self.partner_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    def update_stock(self, shopee_item_id, new_quantity):
        """
        Envia a atualização de estoque para a Shopee.
        """
        path = "/api/v2/product/update_stock"
        timestamp = int(time.time())
        
        # EM PRODUÇÃO: Você precisa implementar o fluxo OAuth para pegar este token real.
        # Para testes locais sem app aprovado, usaremos um placeholder ou token de teste.
        access_token = "seu_access_token_aqui" 

        # Gera a assinatura para esta requisição específica
        sign = self._generate_signature(path, timestamp, access_token)
        
        # Monta a URL completa
        url = f"{self.host}{path}?partner_id={self.partner_id}&timestamp={timestamp}&sign={sign}&shop_id={self.shop_id}&access_token={access_token}"
        
        # Monta o corpo da mensagem (JSON)
        payload = {
            "item_id": int(shopee_item_id),
            "stock_list": [
                {
                    "model_id": 0, # Use 0 se o produto não tiver variações (cor/tamanho)
                    "stock": int(new_quantity)
                }
            ]
        }

        print(f"--- [SHOPEE LOG] Enviando Update ---")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        # --- MODO DE SIMULAÇÃO (SEGURANÇA PARA DESENVOLVIMENTO) ---
        # Como provavelmente você ainda não tem um App Aprovado na Shopee ("Live"),
        # a requisição real falharia. Vamos simular um sucesso para você montar a GUI.
        
        # Para PRODUÇÃO, descomente as linhas abaixo:
        # try:
        #     headers = {"Content-Type": "application/json"}
        #     response = requests.post(url, json=payload, headers=headers, timeout=10)
        #     return response.json()
        # except Exception as e:
        #     return {"error": str(e)}

        # Retorno Simulado
        time.sleep(1) # Simula o tempo da internet
        return {
            "error": "",
            "msg": "Update success (SIMULADO)",
            "response": {
                "item_id": shopee_item_id,
                "stock": new_quantity
            }
        }