from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import mysql.connector
from mysql.connector import Error
import logging
import os
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "csci6651_secret_key"

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "roott",
    "database": "clothing_store"
}

VALID_CATEGORIES = ("Men", "Women", "Kids", "Accessories")


class DatabaseError(Exception):
    pass


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.info("Database connection established.")
        return conn
    except Error as e:
        logger.error(f"[DB ERROR] Could not connect to MySQL: {e}")
        return None


def product_price_generator(products):
    for product in products:
        yield float(product["price"])


def get_cart_total(cart_items):
    return round(sum(map(lambda item: item["price"] * item["qty"], cart_items.values())), 2)


def filter_expensive_products(products, threshold=30.0):
    return list(filter(lambda p: float(p["price"]) > threshold, products))


# ── Homepage ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products ORDER BY id DESC")
        raw_products = cursor.fetchall()
        cursor.close()
        conn.close()
        products = [
            {**p, "price": float(p["price"]), "short_name": p["name"][:20]}
            for p in raw_products
        ]
        logger.info(f"Homepage loaded | {len(products)} products found.")
    return render_template("index.html", products=products)


# ── FEATURE 1: Improved Product Detail Page ───────────────────────────────────

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """
    Improved product detail page showing full info.
    Also fetches related products from the same category.
    """
    conn = get_db_connection()
    product = None
    related = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if product:
            # Fetch related products from same category (exclude current)
            cursor.execute(
                "SELECT * FROM products WHERE category = %s AND id != %s LIMIT 4",
                (product["category"], product_id)
            )
            related = cursor.fetchall()
            related = [{**p, "price": float(p["price"])} for p in related]

        cursor.close()
        conn.close()

    if not product:
        logger.warning(f"Product ID {product_id} not found.")
        flash("Product not found.", "error")
        return redirect(url_for("index"))

    product["price"] = float(product["price"])
    logger.info(f"Product viewed: {product['name']} | ${product['price']:.2f}")
    return render_template("product.html", product=product, related=related)


# ── Category ──────────────────────────────────────────────────────────────────

@app.route("/category/<string:category>")
def category(category):
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
        products = [
            {**p, "price": float(p["price"])}
            for p in raw
            if p["name"] is not None
        ]
    logger.info(f"Category '{category}' | {len(products)} products returned.")
    return render_template("index.html", products=products, active_category=category)


# ── FEATURE 2: Search ─────────────────────────────────────────────────────────

@app.route("/search")
def search():
    """
    Search products by name or description.
    Demonstrates: string methods, SQL LIKE, control flow (Week 3, 4)
    """
    query = request.args.get("q", "").strip()  # Week 4: string strip()

    if not query:
        flash("Please enter a search term.", "info")
        return redirect(url_for("index"))

    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        # SQL LIKE for partial matching
        search_term = f"%{query}%"
        cursor.execute(
            "SELECT * FROM products WHERE name LIKE %s OR description LIKE %s OR category LIKE %s",
            (search_term, search_term, search_term)
        )
        raw = cursor.fetchall()
        cursor.close()
        conn.close()

        # Week 6: List comprehension
        products = [{**p, "price": float(p["price"])} for p in raw]

    logger.info(f"Search: '{query}' | {len(products)} results found.")

    # Week 3: Control flow - different messages based on results
    if not products:
        flash(f"No products found for '{query}'.", "info")
    else:
        flash(f"Found {len(products)} result(s) for '{query}'.", "success")

    return render_template("index.html", products=products, search_query=query)


# ── Cart ──────────────────────────────────────────────────────────────────────

@app.route("/cart")
def cart():
    cart_items = session.get("cart", {})
    total = get_cart_total(cart_items)
    logger.info(f"Cart viewed | {len(cart_items)} items | Total: ${total}")
    return render_template("cart.html", cart=cart_items, total=total)


@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        conn.close()
        if product:
            cart = session.get("cart", {})
            key = str(product_id)
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
            logger.info(f"'{product['name']}' added to cart.")
            # FEATURE 4: Clear validation message
            flash(f'✅ "{product["name"]}" added to cart!', "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/remove_from_cart/<string:key>")
def remove_from_cart(key):
    cart = session.get("cart", {})
    removed_item = cart.pop(key, None)
    session["cart"] = cart
    if removed_item:
        # FEATURE 4: Validation on remove
        flash(f'🗑️ "{removed_item["name"]}" removed from cart.', "info")
        logger.info(f"'{removed_item['name']}' removed from cart.")
    return redirect(url_for("cart"))


@app.route("/clear_cart")
def clear_cart():
    session.pop("cart", None)
    logger.info("Cart cleared.")
    flash("🗑️ Cart cleared.", "info")
    return redirect(url_for("cart"))


# ── FEATURE 3: Update Quantity in Cart ────────────────────────────────────────

@app.route("/update_cart/<string:key>", methods=["POST"])
def update_cart(key):
    """
    Update quantity of a cart item directly from the cart page.
    Demonstrates: control flow, session, data validation (Week 3, 5)
    """
    cart = session.get("cart", {})
    if key in cart:
        try:
            new_qty = int(request.form.get("qty", 1))
            if new_qty <= 0:
                # If qty is 0 or less, remove the item
                item_name = cart[key]["name"]
                cart.pop(key)
                flash(f'🗑️ "{item_name}" removed from cart.', "info")
                logger.info(f"Item '{item_name}' removed via qty=0.")
            else:
                cart[key]["qty"] = new_qty
                flash(f'✅ Quantity updated to {new_qty}.', "success")
                logger.info(f"Cart qty updated: {key} → {new_qty}")
        except ValueError:
            flash("Invalid quantity.", "error")
    session["cart"] = cart
    return redirect(url_for("cart"))


# ── Checkout ──────────────────────────────────────────────────────────────────

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty.", "info")
        return redirect(url_for("cart"))

    if request.method == "POST":
        name    = request.form.get("name")
        email   = request.form.get("email")
        address = request.form.get("address")
        total   = get_cart_total(cart)
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Checkout by {name} at {order_time} | Total: ${total}")

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO orders (customer_name, email, address, total) VALUES (%s, %s, %s, %s)",
                    (name, email, address, total)
                )
                order_id = cursor.lastrowid
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
                flash(f"🎉 Order #{order_id} placed successfully! Thank you, {name}.", "success")
                return redirect(url_for("index"))
            except Error as e:
                logger.error(f"Order failed for {name}: {e}")
                flash(f"Order failed: {e}", "error")
                conn.rollback()

    total = get_cart_total(cart)
    return render_template("checkout.html", cart=cart, total=total)


# ── Admin ──────────────────────────────────────────────────────────────────────

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
        prices = list(product_price_generator(products))
        avg_price = round(sum(prices) / len(prices), 2) if prices else 0
        logger.info(f"Admin panel | {len(products)} products | Avg price: ${avg_price}")
    return render_template("admin.html", products=products)


@app.route("/admin/add", methods=["POST"])
def admin_add():
    name      = request.form["name"].strip()
    price     = request.form["price"]
    category  = request.form["category"]
    image_url = request.form["image_url"].strip()
    desc      = request.form["description"].strip()

    if not name or not price:
        flash("❌ Name and price are required.", "error")
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
        # FEATURE 4: Clear validation on add
        flash(f"✅ Product '{name}' added successfully!", "success")
    return redirect(url_for("admin"))


@app.route("/admin/delete/<int:product_id>")
def admin_delete(product_id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        # Get product name first for validation message
        cursor.execute("SELECT name FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cursor.close()
        conn.close()
        if product:
            logger.info(f"Product '{product['name']}' (ID:{product_id}) deleted.")
            # FEATURE 4: Clear validation on delete with product name
            flash(f"🗑️ Product '{product['name']}' deleted successfully.", "info")
        else:
            flash("Product deleted.", "info")
    return redirect(url_for("admin"))


# ── JSON API ──────────────────────────────────────────────────────────────────

@app.route("/api/products")
def api_products():
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products")
        raw = cursor.fetchall()
        cursor.close()
        conn.close()
        products = [{**p, "price": float(p["price"])} for p in raw]
    logger.info(f"API called | {len(products)} products returned.")
    return jsonify(products)


# ── Search API (JSON) ─────────────────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    """JSON search endpoint."""
    query = request.args.get("q", "").strip()
    conn = get_db_connection()
    products = []
    if conn and query:
        cursor = conn.cursor(dictionary=True)
        search_term = f"%{query}%"
        cursor.execute(
            "SELECT * FROM products WHERE name LIKE %s OR category LIKE %s",
            (search_term, search_term)
        )
        raw = cursor.fetchall()
        cursor.close()
        conn.close()
        products = [{**p, "price": float(p["price"])} for p in raw]
    return jsonify(products)


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("ThreadCo Flask App Starting...")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    app.run(debug=True)
