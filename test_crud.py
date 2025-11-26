import database

def rodar_testes():
    print("--- 1. TESTE DE LEITURA (READ) ---")
    produtos = database.get_all_products()
    for p in produtos:
        print(f"📦 {p['sku']} | {p['nome']} | Estoque: {p['estoque_real']} | Shopee ID: {p['shopee_id']}")
    
    print("\n--- 2. TESTE DE ATUALIZAÇÃO (UPDATE) ---")
    sku_alvo = "TENIS-X"
    novo_estoque = 50
    print(f"Tentando mudar estoque do {sku_alvo} para {novo_estoque}...")
    
    if database.update_stock(sku_alvo, novo_estoque):
        print("✅ Sucesso! Estoque atualizado.")
    else:
        print("❌ Falha na atualização.")

    print("\n--- 3. TESTE DE CRIAÇÃO (CREATE) ---")
    # Tenta adicionar um boné (se já existir, vai dar erro de duplicidade, o que é bom testar)
    database.add_product("BONE-VERMELHO", "Boné Trucker Vermelho", 29.90, 100)

    print("\n--- 4. VERIFICAÇÃO FINAL ---")
    produtos_finais = database.get_all_products()
    for p in produtos_finais:
        # Destaca o produto alterado
        marcador = "   "
        if p['sku'] == "TENIS-X" and p['estoque_real'] == 50: marcador = "✅ "
        if p['sku'] == "BONE-VERMELHO": marcador = "🆕 "
        
        print(f"{marcador}{p['sku']} | Estoque: {p['estoque_real']}")

if __name__ == "__main__":
    rodar_testes()