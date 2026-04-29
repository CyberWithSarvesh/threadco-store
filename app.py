"""
CSCI 6651 - Script Programming with Python
Flask E-Commerce Store - Clothing & Apparel
Concepts used: Flask routing, MySQL DB, OOP, functions, data structures,
               Jinja2 templates (MVC), error handling, JSON, session
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "csci6651_secret_key"   # Required for session (shopping cart)

# ─────────────────────────────────────────────
#  DATABASE CONFIG  ← edit these to match your MySQL Workbench settings
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",          # your MySQL username
    "password": "root",  # your MySQL password
    "database": "clothing_store"
}


def get_db_connection():
    """Return a live MySQL connection (or None on failure)."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None


# ─────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """Homepage – show all products."""
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("index.html", products=products)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """Single product detail page."""
    conn = get_db_connection()
    product = None
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        conn.close()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("index"))
    return render_template("product.html", product=product)


@app.route("/category/<string:category>")
def category(category):
    """Filter products by category (Men / Women / Kids / Accessories)."""
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE category = %s", (category,))
        products = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("index.html", products=products, active_category=category)


# ── Cart ──────────────────────────────────────

@app.route("/cart")
def cart():
    """Display the shopping cart stored in session."""
    cart_items = session.get("cart", {})
    total = sum(item["price"] * item["qty"] for item in cart_items.values())
    return render_template("cart.html", cart=cart_items, total=round(total, 2))


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    """Add one unit of a product to the session cart."""
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
            if key in cart:
                cart[key]["qty"] += 1
            else:
                cart[key] = {
                    "name":  product["name"],
                    "price": float(product["price"]),
                    "image": product["image_url"],
                    "qty":   1
                }
            session["cart"] = cart
            flash(f'"{product["name"]}" added to cart!', "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/remove_from_cart/<string:key>")
def remove_from_cart(key):
    """Remove an item from the cart."""
    cart = session.get("cart", {})
    cart.pop(key, None)
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    flash("Cart cleared.", "info")
    return redirect(url_for("cart"))


# ── Checkout ──────────────────────────────────

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    """Save the order to MySQL and clear the cart."""
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", "info")
        return redirect(url_for("cart"))

    if request.method == "POST":
        name    = request.form.get("name")
        email   = request.form.get("email")
        address = request.form.get("address")
        total   = sum(item["price"] * item["qty"] for item in cart.values())

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Insert order header
                cursor.execute(
                    "INSERT INTO orders (customer_name, email, address, total) VALUES (%s, %s, %s, %s)",
                    (name, email, address, round(total, 2))
                )
                order_id = cursor.lastrowid
                # Insert order items
                for key, item in cart.items():
                    cursor.execute(
                        "INSERT INTO order_items (order_id, product_id, qty, price) VALUES (%s, %s, %s, %s)",
                        (order_id, int(key), item["qty"], item["price"])
                    )
                conn.commit()
                cursor.close()
                conn.close()
                session.pop("cart", None)
                flash(f"Order #{order_id} placed successfully! Thank you, {name}.", "success")
                return redirect(url_for("index"))
            except Error as e:
                flash(f"Order failed: {e}", "error")
                conn.rollback()

    total = sum(item["price"] * item["qty"] for item in cart.values())
    return render_template("checkout.html", cart=cart, total=round(total, 2))


# ── Admin – simple product management ─────────

@app.route("/admin")
def admin():
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
    return render_template("admin.html", products=products)


@app.route("/admin/add", methods=["POST"])
def admin_add():
    name      = request.form["name"]
    price     = request.form["price"]
    category  = request.form["category"]
    image_url = request.form["image_url"]
    desc      = request.form["description"]

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
        flash("Product deleted.", "info")
    return redirect(url_for("admin"))


# ── API endpoint (JSON) ────────────────────────

@app.route("/api/products")
def api_products():
    """Return all products as JSON (demonstrates web services / JSON concept)."""
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        for p in products:
            p["price"] = float(p["price"])   # make JSON-serialisable
        cursor.close()
        conn.close()
    return jsonify(products)


if __name__ == "__main__":
    app.run(debug=True)
