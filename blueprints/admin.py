from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func

from werkzeug.security import check_password_hash

from models import Category, Order, OrderItem, Product, User, db
from security import HASH_FALSO, acertou, bloqueado, falhou

admin = Blueprint("admin", __name__)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = db.session.get(User, session.get("admin_id") or 0)
        if not user or not user.is_admin:
            session.clear()
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapper


@admin.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email, senha = request.form.get("email", "").strip().lower(), request.form.get("password", "")
        if bloqueado(email):
            flash("Muitas tentativas. Aguarde 10 minutos e tente de novo.")
        else:
            user = User.query.filter_by(email=email, is_admin=True).first()
            if check_password_hash(user.password_hash if user else HASH_FALSO, senha) and user:
                acertou(email)
                session.clear()
                session["admin_id"] = user.id
                return redirect(url_for("admin.dashboard"))
            falhou(email)
            flash("E-mail ou senha incorretos. Confira os dados e tente de novo.")
    return render_template("admin/login.html")


@admin.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("shop.index"))


@admin.route("/")
@login_required
def dashboard():
    since = datetime.utcnow() - timedelta(days=29)
    day = func.date(Order.created_at)
    pago = Order.status == "pago"
    daily = (db.session.query(day, func.sum(Order.total)).filter(Order.created_at >= since, pago)
             .group_by(day).order_by(day).all())
    top = (db.session.query(Product.name, func.sum(OrderItem.quantity))
           .join(OrderItem, OrderItem.product_id == Product.id)
           .join(Order, Order.id == OrderItem.order_id).filter(pago)
           .group_by(Product.id, Product.name)
           .order_by(func.sum(OrderItem.quantity).desc()).limit(5).all())
    kpis = {
        "revenue": db.session.query(func.coalesce(func.sum(Order.total), 0))
        .filter(pago).scalar(),
        "orders": Order.query.filter(pago).count(),
        "pending": Order.query.filter_by(status="pendente").count(),
        "products": Product.query.filter_by(active=True).count(),
    }
    return render_template("admin/dashboard.html", kpis=kpis,
                           days=[d.strftime("%d/%m") if hasattr(d, "strftime") else str(d) for d, _ in daily],
                           totals=[float(t) for _, t in daily],
                           top_names=[n for n, _ in top], top_qty=[int(q) for _, q in top])


def ler_produto(f):
    """Valida o formulário de produto. Devolve (dados, mensagem_de_erro)."""
    try:
        preco = Decimal(f.get("price", "").replace(",", ".").strip())
        estoque, categoria = int(f.get("stock", "")), int(f.get("category_id", ""))
    except (InvalidOperation, ValueError):
        return None, "Confira preço, estoque e categoria."
    nome, imagem = f.get("name", "").strip(), f.get("image_url", "").strip()
    if not nome or len(nome) > 160:
        return None, "Informe o nome do produto (até 160 caracteres)."
    if not preco.is_finite() or not 0 <= preco < 100_000_000 or estoque < 0:
        return None, "Preço e estoque não podem ser negativos."
    if imagem and (not imagem.startswith(("http://", "https://")) or len(imagem) > 500):
        return None, "A imagem precisa ser um link http:// ou https://."
    if not db.session.get(Category, categoria):
        return None, "Categoria inválida."
    return dict(name=nome, description=f.get("description", "").strip(), price=preco.quantize(Decimal("0.01")),
                stock=estoque, image_url=imagem, category_id=categoria), None


@admin.route("/products", methods=["GET", "POST"])
@login_required
def products():
    if request.method == "POST":
        dados, erro = ler_produto(request.form)
        if erro:
            flash(erro)
        else:
            db.session.add(Product(**dados))
            db.session.commit()
            flash("Produto cadastrado.")
            return redirect(url_for("admin.products"))
    return render_template("admin/products.html",
                           products=Product.query.order_by(Product.id.desc()).all(),
                           categories=Category.query.order_by(Category.name).all())


@admin.route("/products/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def edit_product(pid):
    p = db.get_or_404(Product, pid)
    if request.method == "POST":
        dados, erro = ler_produto(request.form)
        if erro:
            flash(erro)
        else:
            for campo, valor in dados.items():
                setattr(p, campo, valor)
            p.active = "active" in request.form
            db.session.commit()
            flash("Produto atualizado.")
            return redirect(url_for("admin.products"))
    return render_template("admin/product_edit.html", p=p,
                           categories=Category.query.order_by(Category.name).all())


@admin.route("/products/<int:pid>/toggle", methods=["POST"])
@login_required
def toggle(pid):
    product = db.get_or_404(Product, pid)
    product.active = not product.active
    db.session.commit()
    flash("Produto ativado." if product.active else "Produto desativado.")
    return redirect(url_for("admin.products"))


@admin.route("/orders")
@login_required
def orders():
    return render_template("admin/orders.html", orders=Order.query.order_by(Order.id.desc()).limit(200).all())


@admin.route("/orders/<int:oid>/status", methods=["POST"])
@login_required
def order_status(oid):
    order = db.get_or_404(Order, oid)
    novo = request.form.get("status")
    if novo in ("pendente", "pago", "cancelado") and novo != order.status:
        if novo == "cancelado":  # devolve ao estoque
            for i in order.items:
                i.product.stock += i.quantity
        elif order.status == "cancelado":
            for i in order.items:
                i.product.stock = max(i.product.stock - i.quantity, 0)
        order.status = novo
        db.session.commit()
        flash(f"Pedido #{order.id} marcado como {novo}.")
    return redirect(url_for("admin.orders"))
