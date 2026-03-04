import streamlit as st
import hashlib
import sqlite3
import re
from datetime import datetime
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Savoria — Smart Restaurant AI",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# GLOBAL CSS
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0d0d0d !important;
    color: #f0ece4 !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: #0d0d0d !important;
}

[data-testid="stSidebar"] { display: none !important; }

div.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Auth Page ── */
.auth-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: stretch;
}

.auth-left {
    flex: 1;
    background: linear-gradient(160deg, #1a0a00 0%, #2d1200 40%, #0d0d0d 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 60px 40px;
    position: relative;
    overflow: hidden;
}

.auth-left::before {
    content: '';
    position: absolute;
    width: 500px; height: 500px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(212,120,30,0.15) 0%, transparent 70%);
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
}

.auth-brand {
    font-family: 'Playfair Display', serif;
    font-size: 52px;
    font-weight: 700;
    color: #e8a045;
    letter-spacing: -1px;
    line-height: 1;
    z-index: 1;
}

.auth-brand-tagline {
    font-size: 14px;
    color: rgba(240,236,228,0.5);
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-top: 10px;
    z-index: 1;
}

.auth-left-quote {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: 20px;
    color: rgba(240,236,228,0.35);
    text-align: center;
    margin-top: 60px;
    max-width: 320px;
    line-height: 1.6;
    z-index: 1;
}

.auth-right {
    flex: 0 0 480px;
    background: #111111;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 60px 50px;
    border-left: 1px solid rgba(255,255,255,0.06);
}

.auth-title {
    font-family: 'Playfair Display', serif;
    font-size: 30px;
    font-weight: 600;
    color: #f0ece4;
    margin-bottom: 6px;
}

.auth-subtitle {
    font-size: 14px;
    color: rgba(240,236,228,0.45);
    margin-bottom: 36px;
}

/* ── Input fields ── */
[data-testid="stTextInput"] input {
    background: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #f0ece4 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    padding: 14px 16px !important;
    transition: border-color 0.2s !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: #e8a045 !important;
    box-shadow: 0 0 0 3px rgba(232,160,69,0.12) !important;
}

[data-testid="stTextInput"] label {
    color: rgba(240,236,228,0.6) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
    margin-bottom: 6px !important;
}

/* ── Buttons ── */
[data-testid="stButton"] button {
    background: #e8a045 !important;
    color: #0d0d0d !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 14px 24px !important;
    width: 100% !important;
    transition: background 0.2s, transform 0.1s !important;
    letter-spacing: 0.2px !important;
}

[data-testid="stButton"] button:hover {
    background: #d4903a !important;
    transform: translateY(-1px) !important;
}

[data-testid="stButton"] button:active {
    transform: translateY(0) !important;
}

/* ── Tab switcher (auth) ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #1a1a1a !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    margin-bottom: 28px !important;
    gap: 0 !important;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(240,236,228,0.45) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    border-radius: 7px !important;
    padding: 10px 20px !important;
    flex: 1 !important;
    text-align: center !important;
}

[data-testid="stTabs"] [aria-selected="true"] {
    background: #e8a045 !important;
    color: #0d0d0d !important;
}

[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }

/* ── App Top Bar ── */
.topbar {
    background: #111111;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding: 0 32px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 100;
}

.topbar-logo {
    font-family: 'Playfair Display', serif;
    font-size: 24px;
    font-weight: 700;
    color: #e8a045;
}

.topbar-user {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: rgba(240,236,228,0.6);
}

.topbar-avatar {
    width: 34px; height: 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, #e8a045, #c4702a);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 14px; color: #0d0d0d;
}

/* ── App Layout ── */
.app-layout {
    display: grid;
    grid-template-columns: 260px 1fr 320px;
    min-height: calc(100vh - 64px);
}

/* ── Left Panel (Menu) ── */
.menu-panel {
    background: #111111;
    border-right: 1px solid rgba(255,255,255,0.07);
    padding: 28px 20px;
    overflow-y: auto;
}

.panel-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: rgba(240,236,228,0.3);
    margin-bottom: 16px;
}

.menu-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    border-radius: 12px;
    background: #1a1a1a;
    border: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 10px;
    transition: border-color 0.2s;
}

.menu-item:hover { border-color: rgba(232,160,69,0.3); }

.menu-item-name {
    font-weight: 500;
    font-size: 15px;
    color: #f0ece4;
}

.menu-item-emoji {
    font-size: 20px;
    margin-right: 10px;
}

.menu-item-price {
    font-weight: 600;
    font-size: 14px;
    color: #e8a045;
    background: rgba(232,160,69,0.1);
    padding: 4px 10px;
    border-radius: 20px;
}

/* ── Chat Area ── */
.chat-panel {
    background: #0d0d0d;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

/* ── Right Panel (Bill) ── */
.bill-panel {
    background: #111111;
    border-left: 1px solid rgba(255,255,255,0.07);
    padding: 28px 20px;
    overflow-y: auto;
}

.bill-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.bill-item-name {
    font-size: 14px;
    color: #f0ece4;
    font-weight: 500;
}

.bill-item-time {
    font-size: 11px;
    color: rgba(240,236,228,0.3);
    margin-top: 2px;
}

.bill-item-price {
    font-size: 14px;
    font-weight: 600;
    color: #e8a045;
}

.bill-total {
    background: linear-gradient(135deg, rgba(232,160,69,0.15), rgba(232,160,69,0.05));
    border: 1px solid rgba(232,160,69,0.25);
    border-radius: 12px;
    padding: 18px;
    margin-top: 20px;
    text-align: center;
}

.bill-total-label {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(240,236,228,0.4);
    margin-bottom: 4px;
}

.bill-total-amount {
    font-family: 'Playfair Display', serif;
    font-size: 32px;
    font-weight: 700;
    color: #e8a045;
}

/* ── Chat Messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 0 32px !important;
    margin-bottom: 4px !important;
}

[data-testid="stChatMessage"] > div {
    max-width: 680px !important;
}

[data-testid="stChatMessageContent"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    color: #f0ece4 !important;
}

/* User bubble */
[data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"],
.stChatMessage.user [data-testid="stChatMessageContent"] {
    background: rgba(232,160,69,0.12) !important;
    border: 1px solid rgba(232,160,69,0.2) !important;
    border-radius: 16px 16px 4px 16px !important;
    padding: 14px 18px !important;
}

/* Assistant bubble */
[data-testid="stChatMessage"]:not([data-testid*="user"]) [data-testid="stChatMessageContent"] {
    background: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 16px 16px 16px 4px !important;
    padding: 14px 18px !important;
}

/* ── Chat Input ── */
[data-testid="stChatInput"] {
    background: #111111 !important;
    border-top: 1px solid rgba(255,255,255,0.07) !important;
    padding: 16px 32px !important;
}

[data-testid="stChatInput"] textarea {
    background: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: #f0ece4 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
}

[data-testid="stChatInput"] textarea:focus {
    border-color: #e8a045 !important;
    box-shadow: 0 0 0 3px rgba(232,160,69,0.1) !important;
}

/* ── Alerts ── */
[data-testid="stSuccess"] {
    background: rgba(34,197,94,0.1) !important;
    border: 1px solid rgba(34,197,94,0.25) !important;
    border-radius: 10px !important;
    color: #86efac !important;
}

[data-testid="stInfo"] {
    background: rgba(232,160,69,0.08) !important;
    border: 1px solid rgba(232,160,69,0.2) !important;
    border-radius: 10px !important;
    color: rgba(240,236,228,0.7) !important;
}

[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(255,255,255,0.07) !important;
    margin: 20px 0 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #1a1a1a !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

[data-testid="stMetricLabel"] {
    color: rgba(240,236,228,0.45) !important;
    font-size: 12px !important;
    letter-spacing: 0.5px !important;
}

[data-testid="stMetricValue"] {
    color: #e8a045 !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 28px !important;
}

/* ── Download Button ── */
[data-testid="stDownloadButton"] button {
    background: transparent !important;
    color: #e8a045 !important;
    border: 1px solid rgba(232,160,69,0.35) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 12px 20px !important;
    width: 100% !important;
    transition: all 0.2s !important;
}

[data-testid="stDownloadButton"] button:hover {
    background: rgba(232,160,69,0.1) !important;
    border-color: #e8a045 !important;
    transform: translateY(-1px) !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #e8a045 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(232,160,69,0.25); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(232,160,69,0.45); }

/* ── Column layout for app ── */
[data-testid="stHorizontalBlock"] > div:first-child {
    border-right: 1px solid rgba(255,255,255,0.07);
}

/* ── Logout button override ── */
.logout-btn button {
    background: transparent !important;
    color: rgba(240,236,228,0.4) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    border-radius: 8px !important;
    width: auto !important;
}

.logout-btn button:hover {
    background: rgba(255,255,255,0.05) !important;
    color: #f0ece4 !important;
    transform: none !important;
}
</style>
""", unsafe_allow_html=True)


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

MENU_EMOJI = {
    "pizza": "🍕",
    "burger": "🍔",
    "pasta": "🍝"
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
        return True, "Account created! Please sign in."
    except sqlite3.IntegrityError:
        return False, "Username already taken."

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
# AUTH PAGE (Full-Screen, No Sidebar)
# =====================================================
def show_auth_page():
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        st.markdown("""
        <div style="min-height:100vh; background:linear-gradient(160deg,#1a0a00 0%,#2d1200 40%,#0d0d0d 100%);
             display:flex; flex-direction:column; justify-content:center; align-items:center; padding:60px 40px;">
            <div style="text-align:center;">
                <div style="font-family:'Playfair Display',serif; font-size:56px; font-weight:700; color:#e8a045; line-height:1;">
                    Savoria
                </div>
                <div style="font-size:12px; color:rgba(240,236,228,0.4); letter-spacing:5px; text-transform:uppercase; margin-top:12px;">
                    Smart Restaurant AI
                </div>
                <div style="width:48px; height:2px; background:#e8a045; margin:28px auto;"></div>
                <div style="font-family:'Playfair Display',serif; font-style:italic; font-size:18px; 
                     color:rgba(240,236,228,0.35); max-width:340px; line-height:1.7; margin:0 auto;">
                    "Good food is the foundation of genuine happiness."
                </div>
                <div style="margin-top:48px; display:flex; gap:20px; justify-content:center;">
                    <div style="text-align:center;">
                        <div style="font-family:'Playfair Display',serif; font-size:28px; color:#e8a045; font-weight:700;">3</div>
                        <div style="font-size:11px; color:rgba(240,236,228,0.3); letter-spacing:1px; text-transform:uppercase; margin-top:4px;">Menu Items</div>
                    </div>
                    <div style="width:1px; background:rgba(255,255,255,0.08);"></div>
                    <div style="text-align:center;">
                        <div style="font-family:'Playfair Display',serif; font-size:28px; color:#e8a045; font-weight:700;">AI</div>
                        <div style="font-size:11px; color:rgba(240,236,228,0.3); letter-spacing:1px; text-transform:uppercase; margin-top:4px;">Powered</div>
                    </div>
                    <div style="width:1px; background:rgba(255,255,255,0.08);"></div>
                    <div style="text-align:center;">
                        <div style="font-family:'Playfair Display',serif; font-size:28px; color:#e8a045; font-weight:700;">24/7</div>
                        <div style="font-size:11px; color:rgba(240,236,228,0.3); letter-spacing:1px; text-transform:uppercase; margin-top:4px;">Service</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="min-height:100vh; background:#111111; display:flex; flex-direction:column; 
             justify-content:center; padding:60px 50px; border-left:1px solid rgba(255,255,255,0.06);">
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='padding: 60px 20px 0 20px;'>", unsafe_allow_html=True)

        st.markdown("""
        <p style="font-family:'Playfair Display',serif; font-size:28px; font-weight:600; color:#f0ece4; margin-bottom:4px;">
            Welcome back
        </p>
        <p style="font-size:14px; color:rgba(240,236,228,0.4); margin-bottom:32px;">
            Sign in or create your account below
        </p>
        """, unsafe_allow_html=True)

        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Sign In →", key="login_btn"):
                if username and password:
                    user_id = authenticate_user(username, password)
                    if user_id:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_id = user_id
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.warning("Please fill in all fields.")

        with tab_register:
            new_user = st.text_input("Choose a Username", key="reg_user", placeholder="Pick a unique username")
            new_pass = st.text_input("Create Password", type="password", key="reg_pass", placeholder="Min. 6 characters")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="Repeat password")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("Create Account →", key="reg_btn"):
                if new_user and new_pass and confirm_pass:
                    if new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    elif len(new_pass) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        ok, msg = register_user(new_user, new_pass)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                else:
                    st.warning("Please fill in all fields.")

        st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# SHOW AUTH IF NOT LOGGED IN
# =====================================================
if not st.session_state.logged_in:
    show_auth_page()
    st.stop()


# =====================================================
# AI TOOLS
# =====================================================
@tool
def get_menu(query: str):
    """Returns restaurant menu and prices."""
    return f"Our menu: {MENU} (Prices in tk)"

@tool
def place_order(user_input: str):
    """Extract multiple items and quantities from natural language. Example: '2 pizzas and 1 burger'"""
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

        st.toast(f"Added {qty} × {item} to your order 🛒")
        summary.append(f"{qty} × {item}")

    conn.commit()
    return f"✅ Order Confirmed:\n" + "\n".join(summary) + f"\nTotal: {total_cost} tk"

@tool
def recommend_items(context: str):
    """Suggest popular or complementary items."""
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
        return f"You might also enjoy: {', '.join(suggestions)}"
    return "No recommendations available."

# =====================================================
# AI AGENT
# =====================================================
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

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
def generate_pdf_bill(username, orders, total):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 20)
    p.drawString(200, height - 50, "SAVORIA — RECEIPT")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Customer: {username}")
    p.drawString(50, height - 120, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    p.line(50, height - 130, 550, height - 130)
    p.drawString(50, height - 150, "Item")
    p.drawString(400, height - 150, "Price (tk)")
    p.line(50, height - 155, 550, height - 155)

    y = height - 180
    for item, price, _ in orders:
        p.drawString(50, y, item.capitalize())
        p.drawString(400, y, f"{price}")
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50

    p.line(50, y, 550, y)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y - 30, f"TOTAL: {total} tk")
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(200, 30, "Thank you for dining with Savoria!")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


# =====================================================
# MAIN APP LAYOUT
# =====================================================

# ── Top Bar ──
topbar_col1, topbar_col2 = st.columns([3, 1])

with topbar_col1:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; padding: 12px 0 8px 0;">
        <span style="font-family:'Playfair Display',serif; font-size:26px; font-weight:700; color:#e8a045;">Savoria</span>
        <span style="width:1px; height:22px; background:rgba(255,255,255,0.12);"></span>
        <span style="font-size:13px; color:rgba(240,236,228,0.4); letter-spacing:2px; text-transform:uppercase;">Smart Restaurant AI</span>
    </div>
    """, unsafe_allow_html=True)

with topbar_col2:
    tc1, tc2 = st.columns([2, 1])
    with tc1:
        st.markdown(f"""
        <div style="text-align:right; padding-top:14px; font-size:13px; color:rgba(240,236,228,0.45);">
            👤 <strong style="color:#f0ece4">{st.session_state.username}</strong>
        </div>
        """, unsafe_allow_html=True)
    with tc2:
        st.markdown("<div class='logout-btn' style='padding-top:8px;'>", unsafe_allow_html=True)
        if st.button("Sign out", key="logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='margin:0 0 0 0; border-color:rgba(255,255,255,0.07);'>", unsafe_allow_html=True)

# ── Three-Column Layout ──
left_col, chat_col, right_col = st.columns([0.22, 0.52, 0.26])

# ── LEFT: Menu ──
with left_col:
    st.markdown("""
    <p style="font-size:10px; font-weight:600; letter-spacing:2.5px; text-transform:uppercase; 
       color:rgba(240,236,228,0.3); margin:16px 0 14px 0;">Today's Menu</p>
    """, unsafe_allow_html=True)

    for item, price in MENU.items():
        emoji = MENU_EMOJI.get(item, "🍽️")
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between;
             padding:14px 16px; border-radius:12px; background:#1a1a1a;
             border:1px solid rgba(255,255,255,0.05); margin-bottom:10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:22px;">{emoji}</span>
                <span style="font-weight:500; font-size:15px; color:#f0ece4;">{item.capitalize()}</span>
            </div>
            <span style="font-weight:600; font-size:13px; color:#e8a045; background:rgba(232,160,69,0.1);
                  padding:4px 10px; border-radius:20px;">{price} tk</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:20px 0; border-color:rgba(255,255,255,0.07);'>", unsafe_allow_html=True)

    st.markdown("""
    <p style="font-size:10px; font-weight:600; letter-spacing:2.5px; text-transform:uppercase; 
       color:rgba(240,236,228,0.3); margin-bottom:12px;">Quick Tips</p>
    <p style="font-size:13px; color:rgba(240,236,228,0.4); line-height:1.6;">
        Try asking:<br>
        <em style="color:rgba(232,160,69,0.7);">"Order 2 pizzas"</em><br>
        <em style="color:rgba(232,160,69,0.7);">"What's on the menu?"</em><br>
        <em style="color:rgba(232,160,69,0.7);">"Suggest something for me"</em>
    </p>
    """, unsafe_allow_html=True)

# ── CENTER: Chat ──
with chat_col:
    # Welcome message if empty
    if not st.session_state.messages:
        st.markdown(f"""
        <div style="text-align:center; padding:48px 20px 24px 20px;">
            <div style="font-size:40px; margin-bottom:16px;">🍽️</div>
            <p style="font-family:'Playfair Display',serif; font-size:22px; color:rgba(240,236,228,0.75); margin-bottom:8px;">
                Hello, {st.session_state.username}!
            </p>
            <p style="font-size:14px; color:rgba(240,236,228,0.35); max-width:360px; margin:0 auto; line-height:1.6;">
                I'm your AI dining assistant. Ask me about the menu, place an order, or get personalized recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Ask me anything about our menu…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# AI Processing
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with chat_col:
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                response = agent({"input": st.session_state.messages[-1]["content"]})["output"]
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

# ── RIGHT: Live Bill ──
with right_col:
    st.markdown("""
    <p style="font-size:10px; font-weight:600; letter-spacing:2.5px; text-transform:uppercase; 
       color:rgba(240,236,228,0.3); margin:16px 0 14px 0;">Live Bill</p>
    """, unsafe_allow_html=True)

    current_orders = get_user_orders(st.session_state.user_id)

    if current_orders:
        for item, price, timestamp in current_orders:
            emoji = MENU_EMOJI.get(item, "🍽️")
            time_str = str(timestamp).split('.')[0] if timestamp else ""
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                 padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
                <div>
                    <div style="font-size:14px; color:#f0ece4; font-weight:500;">{emoji} {item.capitalize()}</div>
                    <div style="font-size:11px; color:rgba(240,236,228,0.3); margin-top:2px;">{time_str}</div>
                </div>
                <div style="font-size:14px; font-weight:600; color:#e8a045;">{price} tk</div>
            </div>
            """, unsafe_allow_html=True)

        total_bill = sum(o[1] for o in current_orders)

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(232,160,69,0.15),rgba(232,160,69,0.05));
             border:1px solid rgba(232,160,69,0.25); border-radius:12px; padding:18px 16px;
             text-align:center; margin-top:20px;">
            <div style="font-size:10px; letter-spacing:2px; text-transform:uppercase; 
                 color:rgba(240,236,228,0.4); margin-bottom:6px;">Total Due</div>
            <div style="font-family:'Playfair Display',serif; font-size:32px; font-weight:700; color:#e8a045;">
                {total_bill} tk
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        # PDF Download
        pdf_file = generate_pdf_bill(st.session_state.username, current_orders, total_bill)
        st.download_button(
            label="📄 Download Receipt",
            data=pdf_file,
            file_name=f"savoria_bill_{st.session_state.username}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        if st.button("🗑 Clear Order", use_container_width=True, key="clear_cart"):
            c.execute("DELETE FROM orders WHERE user_id=?", (st.session_state.user_id,))
            conn.commit()
            st.rerun()

    else:
        st.markdown("""
        <div style="text-align:center; padding:40px 16px;">
            <div style="font-size:32px; margin-bottom:12px; opacity:0.3;">🧾</div>
            <p style="font-size:13px; color:rgba(240,236,228,0.3); line-height:1.6;">
                Your order will<br>appear here
            </p>
        </div>
        """, unsafe_allow_html=True)