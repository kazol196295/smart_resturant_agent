import streamlit as st
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

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0d0d0d !important;
    color: #f5f1eb !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stAppViewContainer"] > .main { background: #0d0d0d !important; }
[data-testid="stSidebar"] { display: none !important; }
div.block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

[data-testid="stTextInput"] input {
    background: #1e1e1e !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #f5f1eb !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    padding: 14px 16px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #e8a045 !important;
    box-shadow: 0 0 0 3px rgba(232,160,69,0.12) !important;
}

[data-testid="stButton"] button {
    background: #e8a045 !important;
    color: #0d0d0d !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 24px !important;
    width: 100% !important;
    transition: background 0.2s, transform 0.1s !important;
}
[data-testid="stButton"] button:hover {
    background: #d4903a !important;
    transform: translateY(-1px) !important;
}

[data-testid="stDownloadButton"] button {
    background: transparent !important;
    color: #e8a045 !important;
    border: 1px solid rgba(232,160,69,0.4) !important;
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
}

[data-testid="stChatMessage"] {
    background: transparent !important;
    padding: 4px 24px !important;
}
[data-testid="stChatMessageContent"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.65 !important;
    color: #f5f1eb !important;
}

[data-testid="stChatInput"] textarea {
    background: #1e1e1e !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #f5f1eb !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #e8a045 !important;
    box-shadow: 0 0 0 3px rgba(232,160,69,0.1) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #7a746c !important; }

[data-testid="stSuccess"] {
    background: rgba(34,197,94,0.1) !important;
    border: 1px solid rgba(34,197,94,0.25) !important;
    border-radius: 10px !important;
    color: #a7f3c0 !important;
}
[data-testid="stInfo"] {
    background: rgba(232,160,69,0.08) !important;
    border: 1px solid rgba(232,160,69,0.2) !important;
    border-radius: 10px !important;
    color: #d4c5ad !important;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(232,160,69,0.3); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(232,160,69,0.5); }
</style>
""", unsafe_allow_html=True)


# =====================================================
# DATABASE
# =====================================================
conn = sqlite3.connect("restaurant.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT,
    price REAL,
    timestamp TEXT
)
""")
conn.commit()

# =====================================================
# MENU DATA
# =====================================================
MENU = {"pizza": 500, "burger": 300, "pasta": 400}
MENU_EMOJI = {"pizza": "🍕", "burger": "🍔", "pasta": "🍝"}
POPULAR_ITEMS = ["pizza", "burger"]

# =====================================================
# SESSION STATE
# =====================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =====================================================
# DB HELPERS
# =====================================================
def get_orders():
    c.execute("SELECT item, price, timestamp FROM orders ORDER BY id DESC")
    return c.fetchall()

def clear_orders():
    c.execute("DELETE FROM orders")
    conn.commit()

# =====================================================
# PDF BILL GENERATION
# =====================================================
def generate_pdf_bill(orders, total):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 20)
    p.drawString(180, height - 50, "SAVORIA — RECEIPT")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 90, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    p.line(50, height - 100, 550, height - 100)
    p.drawString(50, height - 120, "Item")
    p.drawString(400, height - 120, "Price (tk)")
    p.line(50, height - 126, 550, height - 126)

    y = height - 150
    for item, price, _ in orders:
        p.drawString(50, y, item.capitalize())
        p.drawString(400, y, f"{price}")
        y -= 22
        if y < 60:
            p.showPage()
            y = height - 50

    p.line(50, y, 550, y)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y - 28, f"TOTAL: {total} tk")
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(190, 30, "Thank you for dining with Savoria!")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


# =====================================================
# AI TOOLS
# =====================================================
@tool
def get_menu(query: str):
    """Returns restaurant menu and prices."""
    return f"Our menu: {MENU} (Prices in tk)"

@tool
def place_order(user_input: str):
    """Extract items and quantities from natural language. Example: '2 pizzas and 1 burger'"""
    text = user_input.lower()
    pattern = r"(\d*)\s*(pizza|burger|pasta)"
    matches = re.findall(pattern, text)

    if not matches:
        return "Could not understand the order. Example: '2 pizzas and 1 burger'"

    total_cost = 0
    summary = []

    for qty_str, item in matches:
        qty = int(qty_str) if qty_str else 1
        price = MENU[item]
        total_cost += price * qty
        for _ in range(qty):
            c.execute(
                "INSERT INTO orders (item, price, timestamp) VALUES (?, ?, ?)",
                (item, price, datetime.now())
            )
        st.toast(f"Added {qty} × {item} to your order 🛒")
        summary.append(f"{qty} × {item}")

    conn.commit()
    return "✅ Order Confirmed:\n" + "\n".join(summary) + f"\nTotal: {total_cost} tk"

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
    return f"You might also enjoy: {', '.join(suggestions)}" if suggestions else "No recommendations available."

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
# TOP BAR
# =====================================================
st.markdown("""
<div style="display:flex; align-items:center; gap:14px; padding:16px 28px 14px 28px;
     border-bottom:1px solid rgba(255,255,255,0.07); background:#0d0d0d;">
    <span style="font-family:'Playfair Display',serif; font-size:26px; font-weight:700; color:#e8a045;">
        Savoria
    </span>
    <span style="width:1px; height:22px; background:rgba(255,255,255,0.15); display:inline-block;"></span>
    <span style="font-size:12px; color:#a09890; letter-spacing:3px; text-transform:uppercase;">
        Smart Restaurant AI
    </span>
</div>
""", unsafe_allow_html=True)


# =====================================================
# MAIN THREE-COLUMN LAYOUT
# =====================================================
left_col, chat_col, right_col = st.columns([0.22, 0.52, 0.26])

# ── LEFT: Menu Panel ──
with left_col:
    st.markdown("""
    <p style="font-size:10px; font-weight:600; letter-spacing:2.5px; text-transform:uppercase;
       color:#a09890; margin:20px 0 14px 12px;">Today's Menu</p>
    """, unsafe_allow_html=True)

    for item, price in MENU.items():
        emoji = MENU_EMOJI.get(item, "🍽️")
        st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between;
             padding:14px 16px; border-radius:12px; background:#181818;
             border:1px solid rgba(255,255,255,0.08); margin:0 8px 10px 8px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:22px;">{emoji}</span>
                <span style="font-weight:500; font-size:15px; color:#f5f1eb;">{item.capitalize()}</span>
            </div>
            <span style="font-weight:600; font-size:13px; color:#e8a045;
                  background:rgba(232,160,69,0.12); padding:4px 10px; border-radius:20px;">
                {price} tk
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:20px 8px; border-color:rgba(255,255,255,0.07);'>", unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:0 12px;">
        <p style="font-size:10px; font-weight:600; letter-spacing:2.5px; text-transform:uppercase;
           color:#a09890; margin-bottom:12px;">Try Asking</p>
        <p style="font-size:13px; color:#c0b8ae; line-height:2.2;">
            <em style="color:rgba(232,160,69,0.9);">"Order 2 pizzas"</em><br>
            <em style="color:rgba(232,160,69,0.9);">"What's on the menu?"</em><br>
            <em style="color:rgba(232,160,69,0.9);">"Suggest something"</em>
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── CENTER: Chat ──
with chat_col:
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center; padding:56px 20px 24px 20px;">
            <div style="font-size:44px; margin-bottom:18px;">🍽️</div>
            <p style="font-family:'Playfair Display',serif; font-size:24px; color:#f5f1eb; margin-bottom:10px;">
                Welcome to Savoria
            </p>
            <p style="font-size:14px; color:#9c9088; max-width:360px; margin:0 auto; line-height:1.7;">
                I'm your AI dining assistant. Ask me about the menu,
                place an order, or get personalized recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask me anything about our menu…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

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
       color:#a09890; margin:20px 0 14px 8px;">Live Bill</p>
    """, unsafe_allow_html=True)

    current_orders = get_orders()

    if current_orders:
        for item, price, timestamp in current_orders:
            emoji = MENU_EMOJI.get(item, "🍽️")
            time_str = str(timestamp).split('.')[0] if timestamp else ""
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                 padding:12px 8px; border-bottom:1px solid rgba(255,255,255,0.07);">
                <div>
                    <div style="font-size:14px; color:#f5f1eb; font-weight:500;">
                        {emoji} {item.capitalize()}
                    </div>
                    <div style="font-size:11px; color:#706860; margin-top:2px;">{time_str}</div>
                </div>
                <div style="font-size:14px; font-weight:600; color:#e8a045;">{price} tk</div>
            </div>
            """, unsafe_allow_html=True)

        total_bill = sum(o[1] for o in current_orders)

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(232,160,69,0.14),rgba(232,160,69,0.04));
             border:1px solid rgba(232,160,69,0.28); border-radius:12px; padding:18px 16px;
             text-align:center; margin:20px 0 14px 0;">
            <div style="font-size:10px; letter-spacing:2px; text-transform:uppercase;
                 color:#b0a898; margin-bottom:6px;">Total Due</div>
            <div style="font-family:'Playfair Display',serif; font-size:34px; font-weight:700; color:#e8a045;">
                {total_bill} tk
            </div>
        </div>
        """, unsafe_allow_html=True)

        pdf_file = generate_pdf_bill(current_orders, total_bill)
        st.download_button(
            label="📄 Download Receipt",
            data=pdf_file,
            file_name="savoria_receipt.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        if st.button("🗑 Clear Order", use_container_width=True, key="clear_cart"):
            clear_orders()
            st.rerun()

    else:
        st.markdown("""
        <div style="text-align:center; padding:48px 16px;">
            <div style="font-size:34px; opacity:0.2; margin-bottom:12px;">🧾</div>
            <p style="font-size:13px; color:#706860; line-height:1.7;">
                Your order will<br>appear here
            </p>
        </div>
        """, unsafe_allow_html=True)