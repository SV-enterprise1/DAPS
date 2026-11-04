from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from models import User, db
from security import HASH_FALSO, acertou, bloqueado, falhou

account = Blueprint("account", __name__)


@account.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        f = request.form
        nome, email, senha = f.get("nome", "").strip(), f.get("email", "").strip().lower(), f.get("senha", "")
        if not nome or "@" not in email or len(email) > 120:
            flash("Informe um nome e um e-mail válidos.")
        elif not 8 <= len(senha) <= 128:
            flash("A senha deve ter entre 8 e 128 caracteres.")
        elif senha != f.get("senha2", ""):
            flash("As senhas não coincidem.")
        else:
            user = User(name=nome[:120], email=email, is_admin=False)
            user.set_password(senha)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Este e-mail já está cadastrado. Tente entrar.")
            else:
                session.clear()
                session["cliente_id"] = user.id
                return redirect(url_for("account.conta"))
    return render_template("shop/cadastro.html")


@account.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email, senha = request.form.get("email", "").strip().lower(), request.form.get("senha", "")
        if bloqueado(email):
            flash("Muitas tentativas. Aguarde 10 minutos e tente de novo.")
        else:
            user = User.query.filter_by(email=email, is_admin=False).first()
            if check_password_hash(user.password_hash if user else HASH_FALSO, senha) and user:
                acertou(email)
                session.clear()
                session["cliente_id"] = user.id
                return redirect(url_for("account.conta"))
            falhou(email)
            flash("E-mail ou senha incorretos.")
    return render_template("shop/entrar.html")


@account.route("/conta")
def conta():
    cliente = db.session.get(User, session.get("cliente_id") or 0)
    if not cliente or cliente.is_admin:
        return redirect(url_for("account.entrar"))
    return render_template("shop/conta.html", cliente=cliente)


@account.route("/sair", methods=["POST"])
def sair():
    session.pop("cliente_id", None)
    return redirect(url_for("shop.index"))
