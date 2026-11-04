import os

_db = os.getenv(
    "DATABASE_URL", "mysql+pymysql://root:senha@localhost:3306/daps?charset=utf8mb4"
)
if _db.startswith("postgres://"):
    _db = _db.replace("postgres://", "postgresql+psycopg2://", 1)
elif _db.startswith("postgresql://"):
    _db = _db.replace("postgresql://", "postgresql+psycopg2://", 1)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-troque-esta-chave")
    SQLALCHEMY_DATABASE_URI = _db
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    # Pagamento: preencha no .env
    PIX_KEY = os.getenv("PIX_KEY", "")
    PIX_NAME = os.getenv("PIX_NAME", "DAPS")
    PIX_CITY = os.getenv("PIX_CITY", "SAO PAULO")
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "")  # só dígitos, ex.: 5511999998888
