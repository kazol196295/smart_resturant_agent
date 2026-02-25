# =========================
# SMART RESTAURANT AI PRO+
# =========================

import streamlit as st
import hashlib
import sqlite3
import re
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import TableStyle
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
import os

st.set_page_config(page_title="Smart Restaurant Pro", layout="wide")

# =========================
# DATABASE
# =========================

conn = sqlite3.connect("restaurant.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    loyalty_points INTEGER DEFAULT 0,
    role TEXT DEFAULT 'user'
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item TEXT,
    quantity INTEGER,
    price REAL,
    timestamp TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item TEXT
)
""")

conn.commit()

# =========================
# MENU
# =========================

MENU = {
    "pizza": 500,
    "burger": 300,
    "pasta": 400
}

# =========================
# AUTH
# =========================

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def register(username, password):
    try:
        c.execute(
            "INSERT INTO users (username, password_hash) VALUES (?,?)",
            (username, hash_password(password))
        )
        conn.commit()
        st.success("Registered successfully")
    except:
        st.error("Username exists")

def login(username, password):
    c.execute("SELECT id, role FROM users WHERE username=? AND password_hash=?",
              (username, hash_password(password)))
    return c.fetchone()

# =========================
# SESSION STATE
# =========================

if "user" not in st.session_state:
    st.session_state.user = None

# =========================
# LOGIN PAGE
# =========================

if not st.session_state.user:
    st.title("Login / Register")

    mode = st.radio("Select", ["Login", "Register"])
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if mode == "Login":
        if st.button("Login"):
            user = login(u, p)
            if user:
                st.session_state.user = {"id": user[0], "role": user[1], "username": u}
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:
        if st.button("Register"):
            register(u, p)

    st.stop()

# =========================
# SIDEBAR MENU + CART
# =========================

user_id = st.session_state.user["id"]
role = st.session_state.user["role"]

st.sidebar.header("Menu")

for item, price in MENU.items():
    col1, col2 = st.sidebar.columns([3,1])
    col1.write(f"{item} - {price}")
    if col2.button("+", key=f"add_{item}"):
        c.execute(
            "INSERT INTO orders (user_id,item,quantity,price,timestamp) VALUES (?,?,?,?,?)",
            (user_id, item, 1, price, datetime.now())
        )
        conn.commit()
        st.toast(f"{item} added")

st.sidebar.divider()
st.sidebar.header("Cart")

c.execute("SELECT id,item,quantity,price FROM orders WHERE user_id=?", (user_id,))
cart = c.fetchall()

total = 0

for oid, item, qty, price in cart:
    col1, col2, col3 = st.sidebar.columns([2,1,1])
    col1.write(f"{item} x{qty}")
    if col2.button("➕", key=f"inc_{oid}"):
        c.execute("UPDATE orders SET quantity=quantity+1 WHERE id=?", (oid,))
        conn.commit()
        st.rerun()
    if col3.button("❌", key=f"del_{oid}"):
        c.execute("DELETE FROM orders WHERE id=?", (oid,))
        conn.commit()
        st.rerun()
    total += qty * price

st.sidebar.success(f"Total: {total}")

# =========================
# LOYALTY POINTS
# =========================

points = total // 100
c.execute("UPDATE users SET loyalty_points = loyalty_points + ? WHERE id=?",
          (points, user_id))
conn.commit()

# =========================
# FAVORITES
# =========================

st.sidebar.divider()
st.sidebar.header("Favorites")

if st.sidebar.button("Save Current Cart as Favorite"):
    for _, item, _, _ in cart:
        c.execute("INSERT INTO favorites (user_id,item) VALUES (?,?)",
                  (user_id, item))
    conn.commit()
    st.toast("Saved as favorite!")

if st.sidebar.button("Order Favorite"):
    c.execute("SELECT item FROM favorites WHERE user_id=?", (user_id,))
    favs = c.fetchall()
    for (item,) in favs:
        c.execute("INSERT INTO orders (user_id,item,quantity,price,timestamp) VALUES (?,?,?,?,?)",
                  (user_id, item, 1, MENU[item], datetime.now()))
    conn.commit()
    st.toast("Favorite ordered!")
    st.rerun()

# =========================
# PDF BILL
# =========================

if st.sidebar.button("Download PDF Bill"):
    file_path = "bill.pdf"
    doc = SimpleDocTemplate(file_path)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Restaurant Bill", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [["Item", "Qty", "Price"]]
    for _, item, qty, price in cart:
        data.append([item, str(qty), str(qty * price)])

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f"Total: {total}", styles["Heading2"]))
    doc.build(elements)

    with open(file_path, "rb") as f:
        st.sidebar.download_button("Download Bill", f, file_name="bill.pdf")

# =========================
# ADMIN DASHBOARD
# =========================

if role == "admin":
    st.title("Admin Dashboard")

    c.execute("SELECT SUM(quantity*price) FROM orders")
    revenue = c.fetchone()[0] or 0
    st.metric("Total Revenue", revenue)

    c.execute("SELECT item, SUM(quantity) FROM orders GROUP BY item")
    data = c.fetchall()

    if data:
        items = [d[0] for d in data]
        qtys = [d[1] for d in data]

        fig = plt.figure()
        plt.bar(items, qtys)
        plt.title("Items Sold")
        st.pyplot(fig)

# =========================
# PAYMENT (Mock Stripe)
# =========================

st.sidebar.divider()
st.sidebar.header("Payment")

if st.sidebar.button("Pay Now (Demo)"):
    if total > 0:
        st.sidebar.success("Payment Successful (Demo)")
        c.execute("DELETE FROM orders WHERE user_id=?", (user_id,))
        conn.commit()
        st.rerun()
    else:
        st.sidebar.warning("Cart is empty")