import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-troque-esta-chave")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "mysql+pymysql://root:senha@localhost:3306/daps?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    # Pagamento: preencha no .env
    PIX_KEY = os.getenv("PIX_KEY", "")
    PIX_NAME = os.getenv("PIX_NAME", "DAPS")
    PIX_CITY = os.getenv("PIX_CITY", "SAO PAULO")
    WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "")  # só dígitos, ex.: 5511999998888
