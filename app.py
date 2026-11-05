import os
import random
from datetime import datetime, timedelta
from decimal import Decimal

import click
from flask import Flask

from config import Config
from models import Category, Order, OrderItem, Product, User, db
from security import init_security
from seed_data import CATEGORIAS, PRODUTOS


def carregar_catalogo_exemplo():
    """Cria categorias, produtos e pedidos de exemplo a partir de seed_data.py."""
    cats = [Category(name=n) for n in CATEGORIAS]
    db.session.add_all(cats)
    db.session.flush()
    prods = [Product(name=n, description="Produto de exemplo.", price=Decimal(p),
                     stock=random.randint(10, 200), category_id=cats[c].id) for n, p, c in PRODUTOS]
    db.session.add_all(prods)
    db.session.flush()
    for _ in range(80):
        quando = datetime.utcnow() - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23))
        pedido = Order(customer_name="Cliente demo", created_at=quando, total=Decimal(0), status="pago")
        for p in random.sample(prods, random.randint(1, 3)):
            qtd = random.randint(1, 3)
            pedido.items.append(OrderItem(product_id=p.id, quantity=qtd, unit_price=p.price))
            pedido.total += p.price * qtd
        db.session.add(pedido)
    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if os.getenv("RENDER"):  # atrás do proxy do Render: IP real do visitante e HTTPS corretos
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    db.init_app(app)
    init_security(app)

    from blueprints.account import account
    from blueprints.admin import admin
    from blueprints.shop import shop

    app.register_blueprint(shop)
    app.register_blueprint(admin, url_prefix=app.config["ADMIN_PATH"])
    app.register_blueprint(account)

    @app.template_filter("brl")
    def brl(value):
        return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @app.cli.command("init-db")
    def init_db():
        """Cria as tabelas, o admin e o catálogo de exemplo."""
        db.create_all()
        if User.query.first():
            return click.echo("Banco já inicializado.")
        admin_user = User(name="Admin DEPIS", email="admin@daps.com", is_admin=True)
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        carregar_catalogo_exemplo()
        click.echo("Pronto! Admin: admin@daps.com / admin123")

    @app.cli.command("trocar-catalogo")
    @click.confirmation_option(prompt="Isto APAGA todos os produtos, categorias e pedidos atuais e carrega o catálogo de seed_data.py. Continuar?")
    def trocar_catalogo():
        """Substitui produtos, categorias e pedidos pelo catálogo de seed_data.py (o admin é mantido)."""
        OrderItem.query.delete()
        Order.query.delete()
        Product.query.delete()
        Category.query.delete()
        db.session.commit()
        carregar_catalogo_exemplo()
        click.echo("Catálogo trocado.")

    @app.cli.command("trocar-senha-admin")
    @click.option("--email", default="admin@daps.com", show_default=True)
    @click.password_option(prompt="Nova senha")
    def trocar_senha_admin(email, password):
        """Define uma nova senha para o administrador (mínimo de 12 caracteres)."""
        user = User.query.filter_by(email=email, is_admin=True).first()
        if not user:
            return click.echo("Administrador não encontrado.")
        if len(password) < 12:
            return click.echo("Use pelo menos 12 caracteres.")
        user.set_password(password)
        db.session.commit()
        click.echo("Senha atualizada.")

    return app


app = create_app()
