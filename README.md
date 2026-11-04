# DEPIS Marketplace (Flask + MySQL)

1. Crie o banco no MySQL: `CREATE DATABASE daps CHARACTER SET utf8mb4;`
2. `python -m venv venv && source venv/bin/activate` (Windows: `venv\Scripts\activate`)
3. `pip install -r requirements.txt`
4. Copie `.env.example` para `.env` e ajuste `DATABASE_URL`
5. Crie as tabelas e os dados de exemplo: importe `daps.sql` (`mysql -u usuario -p < daps.sql`) **ou** rode `flask --app app init-db`
6. `flask --app app run --debug`

Loja: http://127.0.0.1:5000 · Admin: /admin (admin@daps.com / admin123 — troque a senha)

Estrutura: `models.py` (tabelas) · `blueprints/shop.py` (loja) · `blueprints/admin.py` (painel) · `templates/` · `static/style.css`

Trocar o catálogo de exemplo (apaga produtos, categorias e pedidos; mantém o admin):
`flask --app app trocar-catalogo` — os produtos ficam em `seed_data.py`.

Render: comando de início `gunicorn app:app`. Variáveis: SECRET_KEY (forte), DATABASE_URL, PIX_KEY, PIX_NAME, PIX_CITY, WHATSAPP_NUMBER.
Troque a senha do admin: `flask --app app trocar-senha-admin`.
