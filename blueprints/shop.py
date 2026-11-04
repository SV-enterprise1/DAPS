from decimal import Decimal
from urllib.parse import quote

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)

from models import Category, Order, OrderItem, Product, db
from pix import pix_payload, pix_qr_svg

shop = Blueprint("shop", __name__)

METODOS = {"pix": "Pix", "cartao": "Cartão de crédito", "boleto": "Boleto", "whatsapp": "WhatsApp"}


def fmt_brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cart_lines():
    """Itens do carrinho (guardado na sessão) já validados contra o estoque atual."""
    cart = session.get("cart", {})
    if not cart:
        return [], Decimal(0)
    prods = {p.id: p for p in Product.query.filter(
        Product.id.in_([int(i) for i in cart]), Product.active.is_(True)).all()}
    lines, total = [], Decimal(0)
    for pid, qty in cart.items():
        p = prods.get(int(pid))
        if not p or p.stock < 1:
            continue
        qty = min(int(qty), p.stock)
        lines.append({"p": p, "qty": qty, "sub": p.price * qty})
        total += p.price * qty
    return lines, total


@shop.app_context_processor
def inject_cart():
    return {"cart_count": sum(int(q) for q in session.get("cart", {}).values())}


@shop.route("/")
def index():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", type=int)
    query = Product.query.filter_by(active=True)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if cat:
        query = query.filter_by(category_id=cat)
    return render_template("shop/index.html", q=q, cat=cat,
                           products=query.order_by(Product.created_at.desc()).all(),
                           categories=Category.query.order_by(Category.name).all())


# ---------- Carrinho ----------
@shop.post("/carrinho/add")
def cart_add():
    pid = request.form.get("pid", type=int)
    qty = max(request.form.get("qty", 1, type=int), 1)
    p = db.session.get(Product, pid) if pid else None
    if not p or not p.active or p.stock < 1:
        return jsonify(ok=False, msg="Produto indisponível."), 400
    cart = dict(session.get("cart", {}))
    cart[str(p.id)] = min(int(cart.get(str(p.id), 0)) + qty, p.stock)
    session["cart"] = cart
    return jsonify(ok=True, count=sum(cart.values()), msg=f"{p.name} adicionado ao carrinho.")


@shop.get("/carrinho")
def cart():
    lines, total = cart_lines()
    return render_template("shop/cart.html", lines=lines, total=total)


@shop.post("/carrinho/update")
def cart_update():
    pid, qty = request.form.get("pid", type=int), request.form.get("qty", 0, type=int)
    cart = dict(session.get("cart", {}))
    if qty <= 0:
        cart.pop(str(pid), None)
    elif str(pid) in cart:
        cart[str(pid)] = qty
    session["cart"] = cart
    return redirect(url_for("shop.cart"))


# ---------- Checkout ----------
@shop.route("/checkout", methods=["GET", "POST"])
def checkout():
    lines, total = cart_lines()
    if not lines:
        flash("Seu carrinho está vazio.")
        return redirect(url_for("shop.index"))
    if request.method == "POST":
        f = request.form
        d = {k: f.get(k, "").strip() for k in ("name", "email", "phone", "address")}
        metodo = f.get("payment")
        if not all(d.values()) or metodo not in METODOS:
            flash("Preencha todos os campos e escolha a forma de pagamento.")
            return render_template("shop/checkout.html", lines=lines, total=total, metodos=METODOS, f=f)
        order = Order(customer_name=d["name"][:120], customer_email=d["email"][:120],
                      customer_phone=d["phone"][:30], address=d["address"][:300],
                      payment_method=metodo, status="pendente", total=total)
        for l in lines:
            order.items.append(OrderItem(product_id=l["p"].id, quantity=l["qty"], unit_price=l["p"].price))
            l["p"].stock -= l["qty"]
        db.session.add(order)
        db.session.commit()
        session["cart"] = {}
        session["orders"] = (session.get("orders", []) + [order.id])[-20:]
        return redirect(url_for("shop.pedido", oid=order.id))
    return render_template("shop/checkout.html", lines=lines, total=total, metodos=METODOS, f={})


@shop.get("/pedido/<int:oid>")
def pedido(oid):
    if oid not in session.get("orders", []):
        abort(404)
    o = db.get_or_404(Order, oid)
    cfg = current_app.config
    ctx = {}
    if o.payment_method == "pix" and cfg["PIX_KEY"]:
        code = pix_payload(cfg["PIX_KEY"], cfg["PIX_NAME"], cfg["PIX_CITY"], o.total, f"DEPIS{o.id}")
        ctx.update(pix_code=code, pix_qr=pix_qr_svg(code))
    if o.payment_method == "whatsapp" and cfg["WHATSAPP_NUMBER"]:
        itens = "\n".join(f"- {i.quantity}x {i.product.name}" for i in o.items)
        msg = f"Olá! Fiz o pedido #{o.id} na DEPIS.\n{itens}\nTotal: {fmt_brl(o.total)}\nNome: {o.customer_name}"
        ctx["wa_link"] = f"https://wa.me/{cfg['WHATSAPP_NUMBER']}?text={quote(msg)}"
    return render_template("shop/pedido.html", o=o, metodos=METODOS, **ctx)
