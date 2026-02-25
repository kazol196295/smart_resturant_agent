import streamlit as st
import hashlib
import sqlite3
import re
from datetime import datetime
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# ===============================
# 1️⃣ DATABASE SETUP
# ===============================
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

# ===============================
# 2️⃣ MENU
# ===============================
MENU = {
    "pizza": 500,
    "burger": 300,
    "pasta": 400
}

POPULAR_ITEMS = ["pizza", "burger"]

# ===============================
# 3️⃣ SESSION STATE
# ===============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ===============================
# 4️⃣ AUTH FUNCTIONS
# ===============================
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

# ===============================
# 5️⃣ LOGIN UI
# ===============================
def login_ui():
    st.sidebar.title("Login / Register")
    mode = st.sidebar.radio("Mode", ["Login", "Register"])

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if mode == "Login":
        if st.sidebar.button("Login"):
            user_id = authenticate_user(username, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        if st.sidebar.button("Register"):
            register_user(username, password)

if not st.session_state.logged_in:
    login_ui()
    st.stop()

# ===============================
# 6️⃣ AI TOOLS
# ===============================

@tool
def get_menu(query: str):
    """
    Returns the restaurant menu and prices.
    Use when user asks about available food or prices.
    """
    return f"Our menu: {MENU} (Prices in tk)"

@tool
def place_order(user_input: str):
    """
    Parses natural language order like:
    'I want 2 pizzas and 1 burger'
    Extracts items and quantities, saves to DB.
    """

    text = user_input.lower()
    pattern = r"(\d*)\s*(pizza|burger|pasta)"
    matches = re.findall(pattern, text)

    if not matches:
        return "Sorry, I couldn’t understand the order. Example: '2 pizzas and 1 burger'."

    summary = []
    total_cost = 0

    for qty_str, item in matches:
        qty = int(qty_str) if qty_str else 1
        price = MENU[item]
        total_cost += price * qty

        for _ in range(qty):
            c.execute(
                "INSERT INTO orders (user_id, item, price, timestamp) VALUES (?, ?, ?, ?)",
                (st.session_state.user_id, item, price, datetime.now())
            )

        summary.append(f"{qty} x {item}")

    conn.commit()

    return f"✅ Order confirmed:\n" + "\n".join(summary) + f"\nTotal: {total_cost} tk"

@tool
def recommend_items(context: str):
    """
    Suggest popular or complementary items based on user's order.
    """

    suggestions = []

    if "pizza" in context.lower():
        suggestions.append("burger")
    if "burger" in context.lower():
        suggestions.append("pasta")

    for item in POPULAR_ITEMS:
        if item not in context.lower():
            suggestions.append(item)

    suggestions = list(set(suggestions))

    if suggestions:
        return f"You might also like: {', '.join(suggestions)}"
    return "No recommendations available."

# ===============================
# 7️⃣ AI AGENT SETUP
# ===============================
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

tools = [get_menu, place_order, recommend_items]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,
    handle_parsing_errors=True
)

# ===============================
# 8️⃣ MAIN UI
# ===============================
st.title(f"🍕 Smart Restaurant AI - Welcome {st.session_state.username}")

# 🔹 Show Previous Orders
st.subheader("📜 Previous Orders")
orders = get_user_orders(st.session_state.user_id)

if orders:
    for item, price, time in orders:
        st.write(f"- {item} | {price} tk | {time}")
else:
    st.info("No previous orders yet.")

# 🔹 Chat Display
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 🔹 Chat Input
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = agent({"input": prompt})["output"]

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# 🔹 Bill Button
if st.button("💳 Show Total Bill"):
    total = sum(order[1] for order in orders)
    st.success(f"Total Bill: {total} tk")