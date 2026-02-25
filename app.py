# app.py
import streamlit as st
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# -------------------------------
# 1️⃣ Menu Configuration
# -------------------------------
MENU = {
    "pizza": 500,
    "burger": 300,
    "pasta": 400
}

# -------------------------------
# 2️⃣ Define Tools
# -------------------------------
@tool
def get_menu(query: str):
    """
    Returns the restaurant menu and prices.
    Use this tool when the user asks about available dishes or prices.
    """
    return f"Our menu: {MENU} (Prices in tk)"

@tool
def place_order(item: str):
    """
    Confirms an order for a specific item.
    Use this tool when the user mentions a menu item to order.
    """
    item_lower = item.lower()
    if item_lower in MENU:
        return f"Order confirmed: 1 {item_lower}. Total: {MENU[item_lower]} tk."
    return "Sorry, that item isn't on the menu."

# -------------------------------
# 3️⃣ Streamlit UI Setup
# -------------------------------
st.set_page_config(page_title="Smart Restaurant Agent", page_icon="🍕")
st.title("Smart Restaurant AI 🤖")

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 4️⃣ Initialize LLM (Groq)
# -------------------------------
# Make sure GROQ_API_KEY is set in Streamlit Secrets
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0
)

# -------------------------------
# 5️⃣ Setup Memory for Multi-Turn Chat
# -------------------------------
memory = ConversationBufferMemory(
    memory_key="chat_history",  # Required key for this agent type
    return_messages=True
)

# -------------------------------
# 6️⃣ Initialize Agent
# -------------------------------
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
# 7️⃣ Display Chat Messages
# -------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------------
# 8️⃣ Handle User Input
# -------------------------------
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Pass "input" key only — memory handles chat_history automatically
        response = agent({"input": prompt})["output"]
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})