import streamlit as st
import hashlib
import sqlite3
import re
from datetime import datetime
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Smart Restaurant AI",
    page_icon="🍕",
    layout="wide"
)

st.markdown(
    "<style>div.block-container{padding-top:1rem;}</style>",
    unsafe_allow_html=True
)

# =====================================================
# DATABASE
# =====================================================
conn = sqlite3.connect("restaurant.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item TEXT,
    price REAL,
    timestamp TEXT
)
""")

conn.commit()

# =====================================================
# MENU DATA
# =====================================================
MENU = {
    "pizza": 500,
    "burger": 300,
    "pasta": 400
}

POPULAR_ITEMS = ["pizza", "burger"]

# =====================================================
# SESSION STATE
# =====================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# =====================================================
# AUTH FUNCTIONS
# =====================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    try:
        c.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        st.success("Registered successfully! Please login.")
    except sqlite3.IntegrityError:
        st.error("Username already exists.")

def authenticate_user(username, password):
    c.execute(
        "SELECT id FROM users WHERE username=? AND password_hash=?",
        (username, hash_password(password))
    )
    result = c.fetchone()
    return result[0] if result else None

def get_user_orders(user_id):
    c.execute(
        "SELECT item, price, timestamp FROM orders WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    )
    return c.fetchall()

# =====================================================
# LOGIN UI
# =====================================================
def login_ui():
    st.sidebar.title("🔐 Login / Register")
    mode = st.sidebar.radio("Select Mode", ["Login", "Register"])

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if mode == "Login":
        if st.sidebar.button("Login"):
            user_id = authenticate_user(username, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = user_id
                st.toast("Login successful 🎉")
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials")

    else:
        if st.sidebar.button("Register"):
            register_user(username, password)

if not st.session_state.logged_in:
    login_ui()
    st.stop()

# =====================================================
# SIDEBAR - MENU + CART
# =====================================================
st.sidebar.header("📋 Menu")
for item, price in MENU.items():
    st.sidebar.write(f"**{item.capitalize()}** - {price} tk")

st.sidebar.divider()

st.sidebar.header("🛒 Your Cart")

orders = get_user_orders(st.session_state.user_id)

if orders:
    total = 0
    for item, price, _ in orders:
        st.sidebar.write(f"{item} - {price} tk")
        total += price
    st.sidebar.success(f"Total: {total} tk")
else:
    st.sidebar.info("Cart is empty")

if st.sidebar.button("🗑 Clear Cart"):
    c.execute("DELETE FROM orders WHERE user_id=?", (st.session_state.user_id,))
    conn.commit()
    st.sidebar.success("Cart cleared!")
    st.rerun()

# =====================================================
# AI TOOLS
# =====================================================
@tool
def get_menu(query: str):
    """
    Returns restaurant menu and prices.
    """
    return f"Our menu: {MENU} (Prices in tk)"

@tool
def place_order(user_input: str):
    """
    Extract multiple items and quantities from natural language.
    Example: '2 pizzas and 1 burger'
    """

    text = user_input.lower()
    pattern = r"(\d*)\s*(pizza|burger|pasta)"
    matches = re.findall(pattern, text)

    if not matches:
        st.warning("Could not understand the order format.")
        return "Example format: '2 pizzas and 1 burger'"

    total_cost = 0
    summary = []

    for qty_str, item in matches:
        qty = int(qty_str) if qty_str else 1
        price = MENU[item]
        total_cost += price * qty

        for _ in range(qty):
            c.execute(
                "INSERT INTO orders (user_id, item, price, timestamp) VALUES (?, ?, ?, ?)",
                (st.session_state.user_id, item, price, datetime.now())
            )

        st.toast(f"Added {qty} x {item} 🛒")
        summary.append(f"{qty} x {item}")

    conn.commit()
    st.success("Order placed successfully!")

    return f"✅ Order Confirmed:\n" + "\n".join(summary) + f"\nTotal: {total_cost} tk"

@tool
def recommend_items(context: str):
    """
    Suggest popular or complementary items.
    """

    suggestions = []

    if "pizza" in context:
        suggestions.append("burger")
    if "burger" in context:
        suggestions.append("pasta")

    for item in POPULAR_ITEMS:
        if item not in context:
            suggestions.append(item)

    suggestions = list(set(suggestions))

    if suggestions:
        st.info("Showing recommendations 💡")
        return f"You might also like: {', '.join(suggestions)}"
    return "No recommendations available."

# =====================================================
# AI AGENT
# =====================================================
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent = initialize_agent(
    tools=[get_menu, place_order, recommend_items],
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,
    handle_parsing_errors=True
)



# =====================================================
# PDF BILL GENERATION
# =====================================================

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

def generate_pdf_bill(username, orders, total):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFont("Helvetica-Bold", 20)
    p.drawString(200, height - 50, "RESTAURANT RECEIPT")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Customer: {username}")
    p.drawString(50, height - 120, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    p.line(50, height - 130, 550, height - 130)

    # Table Headers
    p.drawString(50, height - 150, "Item")
    p.drawString(400, height - 150, "Price (tk)")
    p.line(50, height - 155, 550, height - 155)

    # Order Items
    y = height - 180
    for item, price, _ in orders:
        p.drawString(50, y, item.capitalize())
        p.drawString(400, y, f"{price}")
        y -= 20
        if y < 50:  # Page break logic
            p.showPage()
            y = height - 50

    # Total
    p.line(50, y, 550, y)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y - 30, f"TOTAL AMOUNT: {total} tk")
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(200, 30, "Thank you for dining with us!")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# =====================================================
# MAIN LAYOUT (CHAT LEFT, HISTORY RIGHT)
# =====================================================
# Create two columns: col1 for Chat (70%), col2 for History/Bill (30%)
col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.title(f"🤖 Smart Restaurant AI")
    st.caption(f"Welcome back, {st.session_state.username} 👋")

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("How can I help you today?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Rerun to show user message immediately before AI thinks
        st.rerun()

# This handles the AI response after the rerun
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with col1:
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI is thinking..."):
                current_prompt = st.session_state.messages[-1]["content"]
                response = agent({"input": current_prompt})["output"]
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                # Rerun to update the Order History in the right column
                st.rerun()

# =====================================================
# RIGHT SIDEBAR / DASHBOARD (ALWAYS UPDATED)
# =====================================================
with col2:
    st.subheader("📜 Live Bill & History")
    current_orders = get_user_orders(st.session_state.user_id)
    
    if current_orders:
        total_bill = sum(order[1] for order in current_orders)
        
        for item, price, time in current_orders:
            st.write(f"**{item.capitalize()}** - {price} tk")
        
        st.divider()
        st.metric(label="Total Amount", value=f"{total_bill} tk")
        
        # --- PDF BILL GENERATION ---
        pdf_file = generate_pdf_bill(st.session_state.username, current_orders, total_bill)
        
        st.download_button(
            label="📄 Download PDF Bill",
            data=pdf_file,
            file_name=f"bill_{st.session_state.username}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.info("No orders yet.")