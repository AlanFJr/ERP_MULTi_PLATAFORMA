import mysql.connector
from mysql.connector import Error
import config  # Importa o nosso arquivo config.py

def testar_conexao():
    print("------------------------------------------------")
    print("🛠️  INICIANDO DIAGNÓSTICO DE CONEXÃO")
    print("------------------------------------------------")
    
    # Passo 1: Verificar se as configurações foram carregadas
    if not config.DB_PASS:
        print("❌ ERRO: A senha não foi carregada. Verifique o arquivo .env")
        return

    print(f"📡 Tentando conectar a: {config.DB_HOST} (Banco: {config.DB_NAME})...")

    connection = None
    try:
        # Passo 2: Tentar estabelecer a conexão (O "Aperto de Mão")
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )

        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"✅ CONEXÃO BEM SUCEDIDA! Versão do MySQL: {db_info}")

            # Passo 3: Criar o Cursor (O funcionário do armazém)
            cursor = connection.cursor()
            
            # Passo 4: Executar uma Query (Pergunta)
            print("\n🔍 Verificando tabela 'produtos'...")
            cursor.execute("SELECT sku, nome, estoque_real FROM produtos")
            
            # Passo 5: Buscar os resultados (Fetch)
            registros = cursor.fetchall()
            
            if len(registros) > 0:
                print(f"   Foram encontrados {len(registros)} produtos:")
                for row in registros:
                    print(f"   ➡️  SKU: {row[0]:<15} | Estoque: {row[2]:<5} | Nome: {row[1]}")
            else:
                print("   ⚠️  A tabela existe, mas está vazia.")

    except Error as e:
        # Tratamento de Erros Robusto
        print("\n❌ FALHA CRÍTICA NA CONEXÃO")
        
        if "Access denied" in str(e):
            print("   Motivo: SENHA OU USUÁRIO INCORRETOS.")
            print("   Ação: Verifique o DB_PASSWORD no arquivo .env")
        elif "Unknown database" in str(e):
            print("   Motivo: O BANCO DE DADOS NÃO EXISTE.")
            print("   Ação: Rode o script SQL do Passo 1 novamente no Workbench.")
        elif "Can't connect" in str(e):
            print("   Motivo: O SERVIDOR MYSQL NÃO ESTÁ RODANDO.")
            print("   Ação: Abra o 'Serviços' do Windows e inicie o MySQL.")
        else:
            print(f"   Erro técnico: {e}")

    finally:
        # Passo 6: Fechar a conexão (Boa prática para liberar memória)
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔒 Conexão encerrada com segurança.")
            print("------------------------------------------------")

if __name__ == "__main__":
    testar_conexao()