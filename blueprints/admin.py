from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func

from models import Category, Order, OrderItem, Product, User, db

admin = Blueprint("admin", __name__)


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapper


@admin.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"], is_admin=True).first()
        if user and user.check_password(request.form["password"]):
            session["admin_id"] = user.id
            return redirect(url_for("admin.dashboard"))
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


@admin.route("/products", methods=["GET", "POST"])
@login_required
def products():
    if request.method == "POST":
        f = request.form
        db.session.add(Product(
            name=f["name"].strip(), description=f["description"].strip(),
            price=Decimal(f["price"].replace(",", ".")), stock=int(f["stock"]),
            image_url=f["image_url"].strip(), category_id=int(f["category_id"])))
        db.session.commit()
        flash("Produto cadastrado.")
        return redirect(url_for("admin.products"))
    return render_template("admin/products.html",
                           products=Product.query.order_by(Product.id.desc()).all(),
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
