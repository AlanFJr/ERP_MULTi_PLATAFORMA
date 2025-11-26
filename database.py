import mysql.connector
from mysql.connector import Error
import config  # Importa as configurações de conexão que criamos antes

def get_db_connection():
    """Função utilitária para abrir conexão com segurança."""
    try:
        connection = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME
        )
        return connection
    except Error as e:
        print(f"Erro crítico ao conectar no MySQL: {e}")
        return None

# --- R (READ) - LER DADOS ---
def get_all_products():
    """
    Retorna uma lista com todos os produtos e seus dados.
    Faz um JOIN para trazer também o ID da Shopee se existir.
    """
    conn = get_db_connection()
    resultados = []
    
    if conn:
        try:
            # dictionary=True faz o banco devolver dados como {'nome': 'Camisa'} ao invés de listas [1, 'Camisa']
            cursor = conn.cursor(dictionary=True) 
            
            query = """
                SELECT p.id, p.sku, p.nome, p.estoque_real, m.remote_item_id as shopee_id 
                FROM produtos p
                LEFT JOIN mapeamento_plataforma m ON p.sku = m.produto_sku AND m.plataforma = 'SHOPEE'
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            
        except Error as e:
            print(f"Erro ao ler produtos: {e}")
            
        finally:
            # O bloco finally garante que a conexão fecha mesmo se der erro
            if conn.is_connected():
                cursor.close()
                conn.close()
                
    return resultados

# --- U (UPDATE) - ATUALIZAR DADOS ---
def update_stock(sku, new_quantity):
    """
    Atualiza a quantidade de estoque de um SKU específico no banco local.
    """
    conn = get_db_connection()
    sucesso = False
    
    if conn:
        try:
            cursor = conn.cursor()
            # O %s é vital para evitar SQL Injection (segurança)
            sql = "UPDATE produtos SET estoque_real = %s WHERE sku = %s"
            
            # Passamos os valores numa tupla (valor, sku)
            cursor.execute(sql, (new_quantity, sku))
            conn.commit() # Salva a alteração permanentemente
            
            if cursor.rowcount > 0:
                sucesso = True
            else:
                print(f"Aviso: SKU '{sku}' não encontrado no banco.")
                
        except Error as e:
            print(f"Erro ao atualizar estoque: {e}")
            
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
                
    return sucesso

# --- C (CREATE) - INSERIR DADOS ---
def add_product(sku, nome, preco, estoque):
    """Insere um novo produto no banco de dados."""
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO produtos (sku, nome, preco, estoque_real) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (sku, nome, preco, estoque))
            conn.commit()
            print(f"Produto '{nome}' adicionado com sucesso!")
            return True
            
        except Error as e:
            print(f"Erro ao inserir produto: {e}")
            return False
            
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
                
    return False