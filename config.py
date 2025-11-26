import os
from dotenv import load_dotenv
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "")  
DB_NAME = os.getenv("DB_NAME", "erp_system")
SHOPEE_URL = os.getenv("SHOPEE_URL")
SHOPEE_PARTNER_ID = os.getenv("SHOPEE_PARTNER_ID")
SHOPEE_PARTNER_KEY = os.getenv("SHOPEE_PARTNER_KEY")
SHOPEE_SHOP_ID = os.getenv("SHOPEE_SHOP_ID")

# Credenciais padrão para usuários limitados e superusuário
DEFAULT_LIMITED_USERNAME = os.getenv("DEFAULT_LIMITED_USERNAME", os.getenv("VALID_USERNAME"))
DEFAULT_LIMITED_PASSWORD = os.getenv("DEFAULT_LIMITED_PASSWORD", os.getenv("VALID_PASSWORD"))
SUPERUSER_USERNAME = os.getenv("SUPERUSER_USERNAME")
SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD")

# Backwards compatibility
VALID_USERNAME = DEFAULT_LIMITED_USERNAME
VALID_PASSWORD = DEFAULT_LIMITED_PASSWORD