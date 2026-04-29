# ThreadCo – Flask Clothing Store
### CSCI 6651 | Script Programming with Python | Spring 2026

---

## 📁 Project Structure

```
flask_store/
│
├── app.py                  ← Main Flask application (routes, DB logic)
├── setup_db.sql            ← MySQL schema + sample data
├── requirements.txt        ← Python packages to install
│
├── templates/              ← Jinja2 HTML templates (View layer)
│   ├── base.html           ← Shared navbar/footer layout
│   ├── index.html          ← Homepage + product grid
│   ├── product.html        ← Product detail page
│   ├── cart.html           ← Shopping cart
│   ├── checkout.html       ← Checkout form
│   └── admin.html          ← Admin panel (add/delete products)
│
└── static/
    └── css/
        └── style.css       ← All styles
```

---

## 🗂️ Syllabus Concepts Used

| Week | Topic               | Where Used                                      |
|------|---------------------|-------------------------------------------------|
| 2    | Data Types / I/O    | Product price formatting, form inputs           |
| 3    | Control Flow        | Cart quantity logic, if/else in templates       |
| 4    | Strings & Slicing   | Flash messages, URL building                    |
| 5    | Data Structures     | `session["cart"]` dictionary, list of products  |
| 8    | Packages / Files    | `mysql.connector`, `flask`, `jsonify`           |
| 9    | OOP                 | Flask `app` object, MySQL connection object     |
| 10   | Functional Python   | `sum()`, `filter()`, `map()` on cart items      |
| 12   | Error Handling      | `try/except` around every DB call               |
| 12   | Web Dev / Flask     | Routes, render_template, request, session       |
| 13   | Flask Templating    | Jinja2 base.html, `{% extends %}`, `{% for %}`  |
| 14   | MVC Application     | Model=MySQL, View=templates, Controller=app.py  |
| 17   | Web Services / JSON | `/api/products` endpoint returns JSON           |

---

## ⚙️ Setup Instructions

### Step 1 – Install Python packages
Open a terminal in VS Code (`Ctrl + \``) and run:
```bash
pip install -r requirements.txt
```

---

### Step 2 – Set up MySQL in Workbench

1. Open **MySQL Workbench** and connect to your local server.
2. Click **File → Open SQL Script** and open `setup_db.sql`.
3. Click the **⚡ lightning bolt** to run it.
4. You should see the `clothing_store` database created with 8 sample products.

---

### Step 3 – Update your DB credentials in `app.py`

Open `app.py` and find this section near the top:

```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",          # ← your MySQL username
    "password": "yourpassword",  # ← your MySQL password
    "database": "clothing_store"
}
```

Replace `yourpassword` with your actual MySQL root password.

---

### Step 4 – Run the Flask app in VS Code

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

Open your browser and go to: **http://localhost:5000**

---

## 🌐 Pages / Routes

| URL                      | Description                          |
|--------------------------|--------------------------------------|
| `/`                      | Homepage – all products              |
| `/category/<name>`       | Filter by Men / Women / Kids / Accessories |
| `/product/<id>`          | Product detail page                  |
| `/cart`                  | Shopping cart (session-based)        |
| `/add_to_cart/<id>`      | Add item to cart (POST)              |
| `/remove_from_cart/<key>`| Remove item from cart                |
| `/checkout`              | Checkout form → saves order to DB    |
| `/admin`                 | Admin panel – add/delete products    |
| `/api/products`          | JSON API – all products              |

---

## 📌 AI Usage Attribution (Academic Integrity)

Per course policy, this project structure was generated with AI assistance (Claude).
The following was AI-assisted:
- Boilerplate Flask route definitions
- HTML/CSS template structure
- SQL schema design

All code has been reviewed, understood, and must be explained by the student.
Refer to syllabus: *"Any usage of external code or LLMs MUST be attributed and documented clearly."*
