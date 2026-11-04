import random
from datetime import datetime, timedelta
from decimal import Decimal

import click
from flask import Flask

from config import Config
from models import Category, Order, OrderItem, Product, User, db
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
    db.init_app(app)

    from blueprints.admin import admin
    from blueprints.shop import shop

    app.register_blueprint(shop)
    app.register_blueprint(admin, url_prefix="/admin")

    @app.template_filter("brl")
    def brl(value):
        return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @app.cli.command("init-db")
    def init_db():
        """Cria as tabelas, o admin e o catálogo de exemplo."""
        db.create_all()
        if User.query.first():
            return click.echo("Banco já inicializado.")
        admin_user = User(name="Admin DAPS", email="admin@daps.com", is_admin=True)
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

    return app


app = create_app()
