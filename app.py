"""
CSCI 6651 - Script Programming with Python
Flask E-Commerce Store - Clothing & Apparel

Syllabus Concepts Covered:
- Week 2:  Data Types, Operators, Basic I/O
- Week 3:  Control Flow, Functions
- Week 4:  Strings and Slicing
- Week 5:  Data Structures (List, Dict, Set, Tuple)
- Week 6:  List Comprehensions
- Week 7:  Packages (os, datetime, logging)
- Week 8:  Object Oriented Python (Flask class, Error class)
- Week 9:  Functional Python (map, filter, sum, lambda)
- Week 10: Generators & Decorators (@app.route)
- Week 11: Error Handling, Testing & Logging
- Week 14: Flask + MVC Application
- Week 15: Flask Templating (Jinja2)
- Week 17: Web Services using JSON
"""

# Week 7: Packages
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
import logging
import os
from datetime import datetime

# Week 11: Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Week 8: OOP - Flask is a Class being instantiated
app = Flask(__name__)
app.secret_key = "csci6651_secret_key"

# Week 2: Data Types - Dictionary for config, Tuple for constants
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "root",
    "database": "clothing_store"
}

# Week 5: Tuple - immutable, cannot be accidentally modified
VALID_CATEGORIES = ("Men", "Women", "Kids", "Accessories")


# Week 8: OOP - Custom Exception Class
class DatabaseError(Exception):
    """Custom exception raised when a database operation fails."""
    pass


# Week 3 & 11: Function with error handling and logging
def get_db_connection():
    """Return a live MySQL connection (or None on failure)."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.info("Database connection established.")
        return conn
    except Error as e:
        logger.error(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None


# Week 10: Generator Function
def product_price_generator(products):
    """Yields one product price at a time - demonstrates generators."""
    for product in products:
        yield float(product["price"])


# Week 9: Functional Python - uses map() and lambda
def get_cart_total(cart_items):
    """Calculate cart total using map() and lambda."""
    return round(sum(map(lambda item: item["price"] * item["qty"], cart_items.values())), 2)


# Week 9: filter() + lambda
def filter_expensive_products(products, threshold=30.0):
    """Return only products above price threshold using filter()."""
    return list(filter(lambda p: float(p["price"]) > threshold, products))


# Week 10: @app.route IS a decorator
@app.route("/")
def index():
    """Homepage - demonstrates list comprehension and logging."""
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        raw_products = cursor.fetchall()
        cursor.close()
        conn.close()

        # Week 6: List Comprehension - build clean product list in one line
        products = [
            {**p, "price": float(p["price"]), "short_name": p["name"][:20]}
            for p in raw_products
        ]
        logger.info(f"Homepage loaded | {len(products)} products found.")

    return render_template("index.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """Single product page - demonstrates string formatting."""
    conn = get_db_connection()
    product = None
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        conn.close()
    if not product:
        # Week 4: f-string formatting
        logger.warning(f"Product ID {product_id} not found.")
        flash("Product not found.", "error")
        return redirect(url_for("index"))
    logger.info(f"Product viewed: {product['name']} | ${product['price']:.2f}")
    return render_template("product.html", product=product)


@app.route("/category/<string:category>")
def category(category):
    """Filter by category - demonstrates control flow and list comprehension."""
    # Week 3: Control Flow - validate input
    if category not in VALID_CATEGORIES:
        flash(f"'{category}' is not a valid category.", "error")
        logger.warning(f"Invalid category: {category}")
        return redirect(url_for("index"))

    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE category = %s", (category,))
        raw = cursor.fetchall()
        cursor.close()
        conn.close()

        # Week 6: List Comprehension with condition
        products = [
            {**p, "price": float(p["price"])}
            for p in raw
            if p["name"] is not None
        ]

    logger.info(f"Category '{category}' | {len(products)} products returned.")
    return render_template("index.html", products=products, active_category=category)


@app.route("/cart")
def cart():
    """Cart page - uses functional get_cart_total()."""
    cart_items = session.get("cart", {})
    total = get_cart_total(cart_items)
    logger.info(f"Cart viewed | {len(cart_items)} items | Total: ${total}")
    return render_template("cart.html", cart=cart_items, total=total)


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    """Add to cart - demonstrates dictionary operations and control flow."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        conn.close()
        if product:
            cart = session.get("cart", {})
            key  = str(product_id)
            # Week 3: Control Flow
            if key in cart:
                cart[key]["qty"] += 1
            else:
                # Week 5: Dictionary creation
                cart[key] = {
                    "name":  product["name"],
                    "price": float(product["price"]),
                    "image": product["image_url"],
                    "qty":   1
                }
            session["cart"] = cart
            logger.info(f"'{product['name']}' added to cart.")
            flash(f'"{product["name"]}" added to cart!', "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/remove_from_cart/<string:key>")
def remove_from_cart(key):
    cart = session.get("cart", {})
    cart.pop(key, None)
    session["cart"] = cart
    logger.info(f"Item {key} removed from cart.")
    return redirect(url_for("cart"))


@app.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    logger.info("Cart cleared.")
    flash("Cart cleared.", "info")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Checkout - demonstrates error handling, datetime, list comprehension."""
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", "info")
        return redirect(url_for("cart"))

    if request.method == "POST":
        name    = request.form.get("name")
        email   = request.form.get("email")
        address = request.form.get("address")
        total   = get_cart_total(cart)

        # Week 7: DateTime package
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Checkout by {name} at {order_time} | Total: ${total}")

        conn = get_db_connection()
        if conn:
            # Week 11: try/except Error Handling
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO orders (customer_name, email, address, total) VALUES (%s, %s, %s, %s)",
                    (name, email, address, total)
                )
                order_id = cursor.lastrowid

                # Week 6: List Comprehension to build order items list
                order_items = [
                    (order_id, int(key), item["qty"], item["price"])
                    for key, item in cart.items()
                ]
                cursor.executemany(
                    "INSERT INTO order_items (order_id, product_id, qty, price) VALUES (%s,%s,%s,%s)",
                    order_items
                )
                conn.commit()
                cursor.close()
                conn.close()
                session.pop("cart", None)
                logger.info(f"Order #{order_id} placed for {name}. Total: ${total}")
                flash(f"Order #{order_id} placed! Thank you, {name}.", "success")
                return redirect(url_for("index"))

            except Error as e:
                # Week 11: Exception caught, logged, transaction rolled back
                logger.error(f"Order failed for {name}: {e}")
                flash(f"Order failed: {e}", "error")
                conn.rollback()

    total = get_cart_total(cart)
    return render_template("checkout.html", cart=cart, total=total)


@app.route("/admin")
def admin():
    """Admin panel - demonstrates generator usage."""
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        products = cursor.fetchall()
        cursor.close()
        conn.close()

        # Week 10: Generator - iterate prices one at a time
        prices = list(product_price_generator(products))
        avg_price = round(sum(prices) / len(prices), 2) if prices else 0
        logger.info(f"Admin panel | {len(products)} products | Avg price: ${avg_price}")

    return render_template("admin.html", products=products)


@app.route("/admin/add", methods=["POST"])
def admin_add():
    """Add product - demonstrates string methods and validation."""
    # Week 4: String Methods - strip() removes extra whitespace
    name      = request.form["name"].strip()
    price     = request.form["price"]
    category  = request.form["category"]
    image_url = request.form["image_url"].strip()
    desc      = request.form["description"].strip()

    # Week 3: Validation with control flow
    if not name or not price:
        flash("Name and price are required.", "error")
        return redirect(url_for("admin"))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, price, category, image_url, description) VALUES (%s,%s,%s,%s,%s)",
            (name, price, category, image_url, desc)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Product added: '{name}' | {category} | ${price}")
        flash("Product added!", "success")
    return redirect(url_for("admin"))


@app.route("/admin/delete/<int:product_id>")
def admin_delete(product_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Product ID {product_id} deleted.")
        flash("Product deleted.", "info")
    return redirect(url_for("admin"))


@app.route("/api/products")
def api_products():
    """JSON API endpoint - demonstrates web services and list comprehension."""
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products")
        raw = cursor.fetchall()
        cursor.close()
        conn.close()

        # Week 6: List Comprehension to format for JSON serialization
        products = [{**p, "price": float(p["price"])} for p in raw]

    logger.info(f"API called | {len(products)} products returned.")
    return jsonify(products)


# Week 3: Main entry point
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("ThreadCo Flask App Starting...")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    app.run(debug=True)
