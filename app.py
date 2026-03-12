import os
import secrets
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash

from blockchain import FakeBlockchain
from db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "landchain-secret-key")
app.config["UPLOAD_FOLDER"] = "/tmp/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.before_request
def ensure_db():
    init_db()


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_email"):
            flash("Please login first.")
            return redirect(url_for("index"))
        return func(*args, **kwargs)

    return wrapper


def get_current_user():
    if not session.get("user_email"):
        return None
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (session["user_email"],)).fetchone()
    conn.close()
    return user


@app.route("/")
def index():
    return render_template("landing.html")


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "demo.user@gmail.com")
    name = request.form.get("name", "Demo User")

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO users (email, name)
        VALUES (?, ?)
        ON CONFLICT(email) DO UPDATE SET name=excluded.name
        """,
        (email, name),
    )
    conn.execute(
        """
        INSERT INTO users (email, name, is_government)
        VALUES ('gov.node@landchain.in', 'Government Node', 1)
        ON CONFLICT(email) DO NOTHING
        """
    )
    conn.commit()
    conn.close()

    session["user_email"] = email
    flash("Logged in with Google (demo mode).")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    return render_template("dashboard.html", user=user)


@app.route("/verify", methods=["POST"])
@login_required
def verify_identity():
    user = get_current_user()
    aadhaar = request.files.get("aadhaar")
    gov_id = request.files.get("gov_id")
    prop_doc = request.files.get("property_doc")

    docs = {}
    for label, f in {"aadhaar": aadhaar, "gov": gov_id, "property": prop_doc}.items():
        if f and f.filename:
            filename = f"{datetime.utcnow().timestamp()}_{label}_{f.filename}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            f.save(path)
            docs[label] = filename

    conn = get_db_connection()
    conn.execute(
        """
        UPDATE users
        SET documents_uploaded = 1,
            identity_verified = 1,
            aadhaar_doc = COALESCE(?, aadhaar_doc),
            gov_id_doc = COALESCE(?, gov_id_doc),
            property_doc = COALESCE(?, property_doc)
        WHERE id = ?
        """,
        (docs.get("aadhaar"), docs.get("gov"), docs.get("property"), user["id"]),
    )
    conn.commit()
    conn.close()

    flash("Government Identity Verified ✅")
    return redirect(url_for("dashboard"))


@app.route("/generate-wallet", methods=["POST"])
@login_required
def generate_wallet():
    user = get_current_user()
    public_key = f"0x{secrets.token_hex(16).upper()}"
    private_key = secrets.token_hex(32)
    wallet_address = f"0x{secrets.token_hex(10).upper()}"

    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET public_key = ?, private_key = ?, wallet_address = ? WHERE id = ?",
        (public_key, private_key, wallet_address, user["id"]),
    )
    conn.commit()
    conn.close()

    flash("Wallet generated successfully.")
    return redirect(url_for("dashboard"))


@app.route("/register-property", methods=["POST"])
@login_required
def register_property():
    user = get_current_user()
    if not user["wallet_address"]:
        flash("Generate wallet first.")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO properties (property_id, title, city, zone, area_sqft, price, owner_wallet, registration_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            f"LC{secrets.randbelow(99999):05}",
            request.form["title"],
            request.form["city"],
            request.form["zone"],
            int(request.form["area_sqft"]),
            int(request.form["price"]),
            user["wallet_address"],
        ),
    )
    conn.commit()
    conn.close()
    flash("Property registration submitted for Government Node approval.")
    return redirect(url_for("marketplace"))


@app.route("/marketplace")
def marketplace():
    filters = {
        "zone": request.args.get("zone", ""),
        "city": request.args.get("city", ""),
        "min_price": request.args.get("min_price", ""),
        "max_price": request.args.get("max_price", ""),
        "min_size": request.args.get("min_size", ""),
    }
    query = "SELECT * FROM properties WHERE registration_status='approved'"
    params = []

    if filters["zone"]:
        query += " AND zone = ?"
        params.append(filters["zone"])
    if filters["city"]:
        query += " AND city = ?"
        params.append(filters["city"])
    if filters["min_price"]:
        query += " AND price >= ?"
        params.append(int(filters["min_price"]))
    if filters["max_price"]:
        query += " AND price <= ?"
        params.append(int(filters["max_price"]))
    if filters["min_size"]:
        query += " AND area_sqft >= ?"
        params.append(int(filters["min_size"]))

    conn = get_db_connection()
    properties = conn.execute(query, params).fetchall()
    conn.close()
    return render_template("marketplace.html", properties=properties, filters=filters)


@app.route("/property/<property_id>")
def property_detail(property_id):
    conn = get_db_connection()
    property_row = conn.execute("SELECT * FROM properties WHERE property_id=?", (property_id,)).fetchone()
    history = conn.execute(
        "SELECT * FROM blocks WHERE property_id=? ORDER BY block_index DESC",
        (property_id,),
    ).fetchall()
    conn.close()
    if not property_row:
        flash("Property not found")
        return redirect(url_for("marketplace"))
    return render_template("property_detail.html", property=property_row, history=history, user=get_current_user())


@app.route("/transfer/<property_id>", methods=["POST"])
@login_required
def transfer_property(property_id):
    buyer_wallet = request.form["buyer_wallet"]
    agreement = request.files.get("sale_agreement")
    agreement_filename = ""
    if agreement and agreement.filename:
        agreement_filename = f"{datetime.utcnow().timestamp()}_agreement_{agreement.filename}"
        agreement.save(os.path.join(app.config["UPLOAD_FOLDER"], agreement_filename))

    conn = get_db_connection()
    prop = conn.execute("SELECT * FROM properties WHERE property_id=?", (property_id,)).fetchone()
    if not prop:
        conn.close()
        flash("Property not found")
        return redirect(url_for("marketplace"))

    conn.execute(
        """
        INSERT INTO transactions (property_id, from_wallet, to_wallet, sale_agreement, status)
        VALUES (?, ?, ?, ?, 'approved')
        """,
        (property_id, prop["owner_wallet"], buyer_wallet, agreement_filename),
    )

    last_block = conn.execute("SELECT * FROM blocks ORDER BY block_index DESC LIMIT 1").fetchone()
    next_index = last_block["block_index"] + 1
    block = FakeBlockchain.create_block(
        index=next_index,
        property_id=property_id,
        from_wallet=prop["owner_wallet"],
        to_wallet=buyer_wallet,
        previous_hash=last_block["hash"],
        sale_agreement=agreement_filename or "N/A",
    )

    conn.execute(
        """
        INSERT INTO blocks (block_index, property_id, from_wallet, to_wallet, timestamp, hash, previous_hash, sale_agreement)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            block["index"],
            block["property_id"],
            block["from_wallet"],
            block["to_wallet"],
            block["timestamp"],
            block["hash"],
            block["previous_hash"],
            block["sale_agreement"],
        ),
    )

    conn.execute("UPDATE properties SET owner_wallet=? WHERE property_id=?", (buyer_wallet, property_id))
    conn.commit()
    conn.close()
    flash("Transaction verified. Block created successfully.")
    return redirect(url_for("ledger"))


@app.route("/ledger")
def ledger():
    conn = get_db_connection()
    blocks = conn.execute("SELECT * FROM blocks ORDER BY block_index DESC").fetchall()
    conn.close()
    return render_template("ledger.html", blocks=blocks)


@app.route("/ledger/block/<int:block_index>")
def ledger_block(block_index):
    conn = get_db_connection()
    block = conn.execute("SELECT * FROM blocks WHERE block_index=?", (block_index,)).fetchone()
    conn.close()
    return render_template("block_detail.html", block=block)


@app.route("/gov")
def government_dashboard():
    conn = get_db_connection()
    pending_props = conn.execute("SELECT * FROM properties WHERE registration_status='pending'").fetchall()
    pending_tx = conn.execute("SELECT * FROM transactions WHERE status='pending'").fetchall()
    conn.close()
    return render_template("government.html", pending_props=pending_props, pending_tx=pending_tx)


@app.route("/gov/approve-property/<property_id>", methods=["POST"])
def approve_property(property_id):
    conn = get_db_connection()
    conn.execute("UPDATE properties SET registration_status='approved' WHERE property_id=?", (property_id,))
    conn.commit()
    conn.close()
    flash("Property approved by Government Node.")
    return redirect(url_for("government_dashboard"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
