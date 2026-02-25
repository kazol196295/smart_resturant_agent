import streamlit as st
# Change the import to use the dedicated groq package
from langchain_groq import ChatGroq 
from langchain.agents import tool, initialize_agent, AgentType

# 1. Menu Configuration (Based on your provided PDF logic)
MENU = {
    "pizza": 500,
    "burger": 300,
    "pasta": 400
}

# 2. Define Tools for the Agent
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

# 3. Streamlit UI Setup
st.set_page_config(page_title="Smart Restaurant Agent", page_icon="🍕")
st.title("Smart Restaurant AI 🤖")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for API Key (Better for deployment)
with st.sidebar:
    api_key = st.text_input("Enter Groq API Key", type="password")
    st.info("Get a free key at console.groq.com")

# 4. Agent Execution Logic
if api_key:
    # Use ChatGroq instead of the community LLM wrapper
    llm = ChatGroq(groq_api_key=api_key, model_name="llama3-8b-8192")
    tools = [get_menu, place_order]
    
    # Initialize the agent
    agent = initialize_agent(
        tools, 
        llm, 
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        # Streamlit needs a way to handle memory across reruns
        handle_parsing_errors=True 
    )

    # Display Chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("How can I help you?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # The agent decides whether to use a tool or just chat
            response = agent.run(input=prompt, chat_history=st.session_state.messages)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.warning("Please enter your Groq API key in the sidebar to start.")