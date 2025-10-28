# app.py
import os
import streamlit as st
import openai
from dotenv import load_dotenv

# ---------------------------
# Load environment / API key
# ---------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Missing OPENAI_API_KEY. Create a .env file with OPENAI_API_KEY=sk-....")
    st.stop()
openai.api_key = OPENAI_API_KEY

# ---------------------------
# Page config & styling
# ---------------------------
st.set_page_config(page_title="GenAI Chat", page_icon="🤖", layout="wide")
st.markdown(
    """
<style>
/* page background */
.reportview-container .main {
    background: linear-gradient(135deg, #0f172a 0%, #0b1220 100%);
    color: #e6eef8;
}
.header {
    text-align:center;
    margin-bottom: 10px;
}
.title {
    font-family: "Segoe UI", Roboto, Arial;
    color: #a5f3fc;
}
.container {
    padding: 8px;
}
.chat-bubble {
    padding: 12px 16px;
    border-radius: 16px;
    max-width: 78%;
    word-wrap: break-word;
    margin: 8px 0;
    display:inline-block;
}
.user {
    background: linear-gradient(90deg,#06b6d4,#4f46e5);
    color: white;
    float: right;
    border-bottom-right-radius: 6px;
}
.bot {
    background: #e6eef8;
    color: #071422;
    float: left;
    border-bottom-left-radius: 6px;
}
.meta {
    font-size: 12px;
    color: #94a3b8;
    margin: 4px 0;
    clear: both;
}
.clearfix { clear: both; }
.sidebar .stButton>button { width:100%; }
</style>
""",
    unsafe_allow_html=True
)

# ---------------------------
# Helper functions
# ---------------------------
def init_session_state():
    if "history" not in st.session_state:
        # history: list of (role, text)
        st.session_state.history = [
            ("bot", "Hello! I am your GenAI assistant. Ask me anything.")
        ]
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = "You are a helpful, concise AI assistant."

def add_message(role: str, text: str):
    st.session_state.history.append((role, text))

def clear_history():
    st.session_state.history = []

def call_openai_chat(system_prompt: str, user_prompt: str, model="gpt-3.5-turbo",
                     temperature=0.7, max_tokens=512):
    """
    Calls OpenAI ChatCompletion and returns assistant text or an error string.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"⚠ Error calling OpenAI API: {e}"

# ---------------------------
# Initialize session
# ---------------------------
init_session_state()

# ---------------------------
# Layout structure
# ---------------------------
left_col, right_col = st.columns([3, 1])

with right_col:
    st.header("Settings")
    st.caption("Adjust model & assistant personality")
    model_name = st.selectbox("Model", options=["gpt-3.5-turbo"], index=0)
    temp = st.slider("Temperature (creativity)", 0.0, 1.0, 0.7, 0.05)
    max_tokens = st.slider("Max tokens", 64, 1024, 512, 64)
    system_prompt_input = st.text_area("System prompt", value=st.session_state.system_prompt, height=120)
    if st.button("Apply system prompt"):
        st.session_state.system_prompt = system_prompt_input
        st.success("System prompt updated.")
    if st.button("Clear chat history"):
        clear_history()
        st.experimental_rerun()

with left_col:
    st.markdown("<div class='header'><h1 class='title'>🤖 GenAI Chat — Professional UI</h1></div>", unsafe_allow_html=True)
    # Chat container
    chat_container = st.container()
    with chat_container:
        for role, text in st.session_state.history:
            if role == "user":
                st.markdown(f"<div class='meta'><b>You</b></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='chat-bubble user'>{st.session_state.get('escape_html', False) and st.markdown or ''}{text}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='meta'><b>Bot</b></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='chat-bubble bot'>{text}</div>", unsafe_allow_html=True)
            st.markdown("<div class='clearfix'></div>", unsafe_allow_html=True)

    # Input
    user_input = st.text_input("Type a message (press Enter to send)", key="user_input")
    send = st.button("Send")

    # Sending logic
    if (send or (user_input and st.session_state.get("auto_send", False))) and user_input.strip():
        user_text = user_input.strip()
        add_message("user", user_text)
        # add a placeholder bot message while thinking
        add_message("bot", "...")
        # Update UI first
        st.experimental_rerun()

# This block runs when placeholder '...' exists as last bot message — handle actual API call outside to avoid nested run
# Find if there is a bot placeholder to replace
if st.session_state.history and st.session_state.history[-1][1] == "...":
    # last user message is just before it
    last_user_msg = None
    # find last user message
    for role, text in reversed(st.session_state.history[:-1]):
        if role == "user":
            last_user_msg = text
            break
    if last_user_msg is not None:
        # call OpenAI
        with st.spinner("Generating response..."):
            bot_reply = call_openai_chat(st.session_state.system_prompt, last_user_msg,
                                        model=model_name, temperature=temp, max_tokens=max_tokens)
        # replace last placeholder
        st.session_state.history[-1] = ("bot", bot_reply)
        st.experimental_rerun()