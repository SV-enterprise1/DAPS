-- Rode UMA vez no banco que você já importou (MySQL 8+):
--   mysql -u usuario -p daps < migracao_pedidos.sql
ALTER TABLE `order`
  ADD COLUMN customer_email VARCHAR(120) DEFAULT '',
  ADD COLUMN customer_phone VARCHAR(30) DEFAULT '',
  ADD COLUMN address VARCHAR(300) DEFAULT '',
  ADD COLUMN payment_method VARCHAR(20) DEFAULT '',
  ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pendente';
-- Pedidos de exemplo que já existiam contam como pagos nos gráficos
UPDATE `order` SET status = 'pago';
