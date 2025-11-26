from shopee_client import ShopeeClient

def testar_integracao():
    print("--- TESTE DE CLIENTE SHOPEE ---")
    
    # 1. Inicializa o cliente
    client = ShopeeClient()
    
    print(f"Configurado para Partner ID: {client.partner_id}")
    
    # 2. Dados de teste
    # ID fictício de um produto na Shopee
    id_produto_fake = 111222333 
    novo_estoque = 50
    
    # 3. Tenta atualizar
    print(f"\nTentando atualizar produto {id_produto_fake} para estoque {novo_estoque}...")
    resultado = client.update_stock(id_produto_fake, novo_estoque)
    
    # 4. Analisa o resultado
    if resultado.get("error"):
        print(f"❌ Falha: {resultado['error']}")
    else:
        print(f"✅ Sucesso! Resposta da API: {resultado['msg']}")

if __name__ == "__main__":
    testar_integracao()