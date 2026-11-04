import hmac
import secrets
import time

from flask import abort, request, session
from werkzeug.security import generate_password_hash

MAX_FALHAS, BLOQUEIO_S = 5, 600
_falhas = {}  # (ip, e-mail) -> [falhas, bloqueado_até]; fica na memória deste processo
HASH_FALSO = generate_password_hash("senha-falsa")  # iguala o tempo quando o e-mail não existe

CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
       "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "img-src 'self' https: data:; frame-ancestors 'none'; form-action 'self'; base-uri 'self'")


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def _chave(email):
    return (request.remote_addr, email.lower())


def bloqueado(email):
    reg = _falhas.get(_chave(email))
    return bool(reg and reg[1] > time.time())


def falhou(email):
    reg = _falhas.setdefault(_chave(email), [0, 0])
    reg[0] += 1
    if reg[0] >= MAX_FALHAS:
        reg[0], reg[1] = 0, time.time() + BLOQUEIO_S


def acertou(email):
    _falhas.pop(_chave(email), None)


def init_security(app):
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def checar_csrf():
        if request.method == "POST":
            enviado = request.form.get("_csrf", "").encode()
            esperado = session.get("_csrf", "").encode()
            if not esperado or not hmac.compare_digest(enviado, esperado):
                abort(400, "Formulário expirado ou inválido. Volte, recarregue a página e tente de novo.")

    @app.after_request
    def cabecalhos(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Content-Security-Policy", CSP)
        return resp
