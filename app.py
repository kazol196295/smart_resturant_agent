import streamlit as st
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent, AgentType

# -------------------------------
# 1️⃣ Menu Configuration
# -------------------------------
MENU = {
    "pizza": 500,
    "burger": 300,
    "pasta": 400
}

# -------------------------------
# 2️⃣ Define Tools for the Agent
# -------------------------------
@tool
def get_menu(query: str):
    """Returns the restaurant menu and prices."""
    return f"Our menu: {MENU} (Prices in tk)"

@tool
def place_order(item: str):
    """Confirms an order for a specific item."""
    item_lower = item.lower()
    if item_lower in MENU:
        return f"Order confirmed: 1 {item_lower}. Total: {MENU[item_lower]} tk."
    return "Sorry, that item isn't on the menu."

# -------------------------------
# 3️⃣ Streamlit UI Setup
# -------------------------------
st.set_page_config(page_title="Smart Restaurant Agent", page_icon="🍕")
st.title("Smart Restaurant AI 🤖")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 4️⃣ Initialize LLM (Groq)
# -------------------------------
# NOTE: API key must be set in Streamlit Cloud Secrets as GROQ_API_KEY
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0
)

tools = [get_menu, place_order]

# Conversation memory is handled internally by the agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

# -------------------------------
# 5️⃣ Display chat messages
# -------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------------
# 6️⃣ Chat input and agent response
# -------------------------------
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Use dict interface to satisfy input key validation
        response = agent({"input": prompt})["output"]
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})