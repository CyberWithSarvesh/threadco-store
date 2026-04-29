-- ============================================================
--  CSCI 6651 – Clothing Store  |  MySQL Setup Script
--  Run this in MySQL Workbench before starting the Flask app
-- ============================================================

-- 1. Create (or switch to) the database
CREATE DATABASE IF NOT EXISTS clothing_store;
USE clothing_store;

-- 2. Products table
CREATE TABLE IF NOT EXISTS products (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)   NOT NULL,
    price       DECIMAL(10,2)  NOT NULL,
    category    VARCHAR(50)    NOT NULL,   -- Men | Women | Kids | Accessories
    image_url   VARCHAR(255),
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Orders table
CREATE TABLE IF NOT EXISTS orders (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100)  NOT NULL,
    email         VARCHAR(100)  NOT NULL,
    address       TEXT          NOT NULL,
    total         DECIMAL(10,2) NOT NULL,
    ordered_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Order items table (links orders ↔ products)
CREATE TABLE IF NOT EXISTS order_items (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    order_id   INT            NOT NULL,
    product_id INT            NOT NULL,
    qty        INT            NOT NULL DEFAULT 1,
    price      DECIMAL(10,2)  NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 5. Sample products (using free Unsplash placeholder URLs)
INSERT INTO products (name, price, category, image_url, description) VALUES
('Classic White Tee',        19.99, 'Men',         'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400', 'Soft 100% cotton everyday tee.'),
('Slim Fit Chinos',          49.99, 'Men',         'https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400', 'Versatile slim chinos for any occasion.'),
('Floral Summer Dress',      59.99, 'Women',       'https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400', 'Light floral print, perfect for summer.'),
('Cozy Knit Sweater',        45.00, 'Women',       'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=400', 'Warm and stylish ribbed knit sweater.'),
('Kids Denim Jacket',        35.00, 'Kids',        'https://images.unsplash.com/photo-1522771930-78848d9293e8?w=400', 'Durable and cute denim jacket for kids.'),
('Kids Graphic Tee',         14.99, 'Kids',        'https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=400', 'Fun graphic tee kids will love.'),
('Leather Belt',             24.99, 'Accessories', 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400', 'Genuine leather belt with classic buckle.'),
('Canvas Tote Bag',          29.99, 'Accessories', 'https://images.unsplash.com/photo-1544816155-12df9643f363?w=400', 'Eco-friendly everyday carry tote.');
