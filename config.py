import os

_SEGREDO = os.getenv("SECRET_KEY", "dev-troque-esta-chave")
_PRODUCAO = os.getenv("APP_ENV") == "production" or bool(os.getenv("RENDER"))  # o Render define RENDER sozinho
if _PRODUCAO and _SEGREDO.startswith(("dev-", "troque")):
    raise RuntimeError("Defina uma SECRET_KEY forte nas variáveis de ambiente antes de rodar em produção.")


def _db_url():
    url = os.getenv("DATABASE_URL", "mysql+pymysql://root:senha@localhost:3306/daps?charset=utf8mb4")
    if url.startswith("postgres://"):  # o Render entrega assim; o SQLAlchemy exige postgresql://
        url = "postgresql://" + url[len("postgres://"):]
    return url


def _admin_path():
    """Endereço secreto do painel. Defina ADMIN_PATH (ex.: /painel-k7x92qf) para que ninguém adivinhe a URL."""
    p = "/" + os.getenv("ADMIN_PATH", "/admin").strip().strip("/")
    return p if p != "/" else "/admin"


class Config:
    ADMIN_PATH = _admin_path()
    SECRET_KEY = _SEGREDO
    SQLALCHEMY_DATABASE_URI = _db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = _PRODUCAO or os.getenv("COOKIE_SECURE") == "1"
    MAX_CONTENT_LENGTH = 1_000_000
    # Pagamento: preencha no .env (ou nas variáveis de ambiente do Render)
    PIX_KEY = os.getenv("PIX_KEY", "")
    PIX_NAME = os.getenv("PIX_NAME", "DEPIS")
    PIX_CITY = os.getenv("PIX_CITY", "SAO PAULO")
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "")  # só dígitos, ex.: 5511999998888
