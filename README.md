# 🍽️ Smart Restaurant Agent

An intelligent AI-powered restaurant ordering and management system built with **Streamlit**, **LangChain**, and **Groq LLM**.

🔗 **Live Demo:** [Smart Restaurant Agent on Streamlit Cloud](https://smartresturantagent-kazol196295.streamlit.app/)

---

## 🚀 Overview

Smart Restaurant Agent is an advanced food ordering system powered by AI that enables customers to order using natural language while providing restaurant administrators with comprehensive analytics and revenue insights.

The application seamlessly integrates AI chat capabilities, cart management, billing, user authentication, and analytics dashboards into a single, user-friendly platform.

---

## ✨ Features

### 🤖 AI Chat Ordering
- **Natural Language Understanding** - Order by simply describing what you want
  - Example: "I want 2 pizzas and a burger"
- Automatic extraction of multiple items
- Smart menu recommendations
- Add-on and customization suggestions
- Conversation memory for context awareness
- Support for multiple Groq language models (Llama 3, Mixtral)

### 🛒 Smart Cart System
- Add/remove items with ease
- Modify item quantities
- Remove individual items
- Save favorite orders
- Real-time total calculation with tax

### 💳 Billing & Orders
- Comprehensive order summaries
- Download PDF invoices with ReportLab
- Loyalty points program
- Complete order history
- SQLite database for persistent storage

### 📊 Admin Dashboard
- Revenue analytics and trends
- Order statistics and insights
- Sales visualization charts
- Customer behavior analytics

### 👤 Authentication
- User registration with secure password hashing
- Session-based login system
- Admin access control
- Secure credential storage

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | [Streamlit](https://streamlit.io/) |
| **AI/ML Framework** | [LangChain](https://github.com/langchain-ai/langchain) |
| **LLM Provider** | [Groq](https://groq.com/) |
| **Language Models** | Llama 3, Mixtral |
| **Database** | SQLite |
| **PDF Generation** | ReportLab |
| **Data Visualization** | Matplotlib, Streamlit Charts |
| **Memory Management** | LangChain ConversationBufferMemory |
| **HTTP Client** | httpx |

---

## 📂 Project Structure

```
smart_resturant_agent/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── runtime.txt           # Python runtime version
└── README.md             # This file
```

---

## 🔑 Prerequisites

Before you begin, ensure you have the following:
- Python 3.9 or higher
- A [Groq API key](https://console.groq.com/) (free account)
- Git (for cloning the repository)
- A Streamlit Community Cloud account (for deployment)

---

## ⚙️ Installation & Setup

### Option 1: Local Development Setup

#### Step 1️⃣ - Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/smart_resturant_agent.git
cd smart_resturant_agent
```

#### Step 2️⃣ - Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3️⃣ - Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4️⃣ - Set Up Groq API Key

Create a `.streamlit/secrets.toml` file in your project directory:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

**To get your Groq API key:**
1. Visit [Groq Console](https://console.groq.com/)
2. Create a free account
3. Generate an API key
4. Copy and paste it into `secrets.toml`

#### Step 5️⃣ - Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## ☁️ Deployment on Streamlit Cloud

Streamlit Cloud makes it easy to deploy your app with CI/CD capabilities.

### Deployment Steps:

#### 1️⃣ Push to GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

#### 2️⃣ Connect to Streamlit Cloud
1. Go to [Streamlit Community Cloud](https://streamlit.io/cloud)
2. Click **"New app"**
3. Select your GitHub repository
4. Choose the branch (usually `main`)
5. Set the main file path: `app.py`
6. Click **"Deploy"**

#### 3️⃣ Add Groq API Key
1. After deployment, click **Settings** ⚙️
2. Go to **Secrets**
3. Add your Groq API key:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   ```
4. Click **Save**

#### 4️⃣ View Your Live App
Your app is now live at: `https://<username>-<appname>.streamlit.app/`

---

## 🔧 Groq Configuration

### Supported Models

The application supports multiple Groq LLM models:

| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| **mixtral-8x7b-32768** | ⚡ Fast | Good | General ordering, quick responses |
| **llama-3-70b-8192** | Medium | Excellent | Complex queries, recommendations |
| **llama-3-8b-8192** | ⚡⚡ Very Fast | Good | Simple tasks, fast turnaround |

### API Rate Limits

Groq's free tier includes:
- **9000 requests per minute** for paid APIs
- **Pay-as-you-go** pricing

### Setting API Key

The app reads the Groq API key from:
```python
groq_api_key = st.secrets.get("GROQ_API_KEY")
```

Make sure to set this in:
- **Local:** `.streamlit/secrets.toml`
- **Cloud:** Streamlit Cloud Secrets Manager

---

## 🚀 Usage Guide

### For Customers:

1. **Register/Login** - Create an account or log in
2. **Browse Menu** - View available items
3. **AI Chat Ordering** - Use natural language:
   - "I want a pizza and a coke"
   - "Can you recommend something spicy?"
   - "Add a burger to my order"
4. **Review Cart** - Check items and modify quantities
5. **Checkout** - Complete payment and download invoice

### For Administrators:

1. **Login as Admin** - Use admin credentials
2. **View Dashboard** - See analytics and revenue
3. **Order Statistics** - Track sales trends
4. **Customer Insights** - Analyze ordering patterns

---

## 📦 Dependencies

All dependencies are listed in `requirements.txt`:

```
streamlit==1.32.2
langchain==0.1.16
langchain-community==0.0.34
langchain-groq==0.1.4
groq==0.9.0
httpx==0.27.0
pydantic==1.10.13
matplotlib==3.7.2
reportlab==3.5.68
```

Install them with:
```bash
pip install -r requirements.txt
```

---

## 🎯 Environment Variables

Create `.streamlit/secrets.toml` for local development:

```toml
# Groq API Configuration
GROQ_API_KEY = "gsk_your_api_key_here"

# Optional: Model preference
DEFAULT_MODEL = "mixtral-8x7b-32768"
```

For **Streamlit Cloud**, add these in:
- **Settings** → **Secrets** → (paste above)

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Invalid API Key" | Verify your Groq API key in secrets |
| "Module not found" | Run `pip install -r requirements.txt` |
| "streamlit: command not found" | Activate virtual environment: `source venv/bin/activate` |
| "Database locked" | Restart the app and clear cache |
| "Slow responses" | Switch to a faster model in Groq settings |

---

## 📝 License

This project is open source and available under the MIT License.

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Contact & Support

- **Issues:** Create an issue on GitHub
- **Questions:** Open a discussion thread
- **Email:** kazol196295@gmail.com

---

## 🙏 Acknowledgments

- Streamlit for the amazing web framework
- Groq for ultra-fast LLM inference
- LangChain for orchestration capabilities
- Open source community for tools and libraries

---

**Happy Ordering! 🍕🍔🍜**
