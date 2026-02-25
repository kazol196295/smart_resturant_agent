# app.py
import streamlit as st
import hashlib
import sqlite3
from datetime import datetime
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# -------------------------------
# 1️⃣ Database Setup
# -------------------------------
conn = sqlite3.connect("restaurant.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT
)
""")

# Orders table
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

# -------------------------------
# 2️⃣ Streamlit Session State
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 3️⃣ Helper Functions
# -------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    pw_hash = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pw_hash))
        conn.commit()
        st.success("User registered! Please login.")
    except sqlite3.IntegrityError:
        st.error("Username already exists.")

def authenticate_user(username, password):
    pw_hash = hash_password(password)
    c.execute("SELECT id FROM users WHERE username=? AND password_hash=?", (username, pw_hash))
    result = c.fetchone()
    if result:
        return result[0]
    return None

def get_user_orders(user_id):
    c.execute("SELECT item, price, timestamp FROM orders WHERE user_id=? ORDER BY id DESC", (user_id,))
    return c.fetchall()

# -------------------------------
# 4️⃣ Login / Registration UI
# -------------------------------
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
            else:
                st.sidebar.error("Invalid username or password")
    else:
        if st.sidebar.button("Register"):
            register_user(username, password)

if not st.session_state.logged_in:
    login_ui()
    st.stop()

# -------------------------------
# 5️⃣ Restaurant Menu
# -------------------------------
MENU = {
    "pizza": 500,
    "burger": 300,
    "pasta": 400
}

# -------------------------------
# 6️⃣ Define Tools
# -------------------------------
@tool
def get_menu(query: str):
    return f"Our menu: {MENU} (Prices in tk)"

@tool
def place_order(item: str):
    item_lower = item.lower()
    if item_lower in MENU:
        # Save to DB
        c.execute("INSERT INTO orders (user_id, item, price, timestamp) VALUES (?, ?, ?, ?)",
                  (st.session_state.user_id, item_lower, MENU[item_lower], datetime.now()))
        conn.commit()
        return f"Order confirmed: 1 {item_lower}. Total: {MENU[item_lower]} tk."
    return "Sorry, that item isn't on the menu."

# -------------------------------
# 7️⃣ Initialize LLM + Agent
# -------------------------------
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

tools = [get_menu, place_order]
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# -------------------------------
# 8️⃣ Streamlit UI
# -------------------------------
st.title(f"Smart Restaurant AI 🍕 - Welcome {st.session_state.username}")

# Show previous orders
st.subheader("Your Previous Orders")
orders = get_user_orders(st.session_state.user_id)
if orders:
    for o in orders:
        st.markdown(f"- {o[0]}: {o[1]} tk (Ordered at {o[2]})")
else:
    st.info("No previous orders.")

# Chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Pass only "input"; memory handles chat_history
        response = agent({"input": prompt})["output"]
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# -------------------------------
# 9️⃣ Generate Current Session Bill
# -------------------------------
if st.button("Show Current Bill"):
    current_orders = get_user_orders(st.session_state.user_id)
    if current_orders:
        total = sum([o[1] for o in current_orders])
        bill_text = "\n".join([f"{o[0]}: {o[1]} tk" for o in current_orders])
        st.info(f"Your Bill:\n{bill_text}\n\nTotal: {total} tk")
    else:
        st.info("No orders yet.")