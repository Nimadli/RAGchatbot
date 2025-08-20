import streamlit as st
import requests

st.set_page_config(page_title="RAG Chatbot", layout="centered")
st.title("💬 RAG Chatbot")

# Sidebar settings
st.sidebar.header("⚙️ Settings")
mode = st.sidebar.radio("Choose mode:", ["Stream LLM", "Stream Knowledge Base"])
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Custom CSS for dark mode
st.markdown(
    """
    <style>
    .user-bubble {
        background-color: #2E7D32; 
        color: white;
        padding: 8px 12px;
        border-radius: 15px;
        display: inline-block;
        max-width: 80%;
    }
    .bot-bubble {
        background-color: #424242; 
        color: white;
        padding: 8px 12px;
        border-radius: 15px;
        display: inline-block;
        max-width: 80%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper to format messages for backend
def format_messages_for_backend(messages):
    return [{"role": "user" if sender=="You" else "assistant", "content": msg} 
            for sender, msg in messages]

# Chat container
chat_container = st.container()
with chat_container:
    if st.session_state.messages:
        # display all messages (no live answer duplication)
        for sender, msg in st.session_state.messages:
            if sender == "You":
                st.markdown(
                    f"<div style='text-align:right; margin:5px;'><span class='user-bubble'>{msg}</span></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='text-align:left; margin:5px;'><span class='bot-bubble'>{msg}</span></div>",
                    unsafe_allow_html=True,
                )

# Input form (Enter = submit)
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("Ask something:", key="input", label_visibility="collapsed")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.messages.append(("You", user_input))
    history = format_messages_for_backend(st.session_state.messages)

    # Select endpoint
    if mode == "Stream LLM":
        url = "http://localhost:8000/llm/stream"
        with st.spinner("🤖 Bot is typing..."):
            placeholder = st.empty()
            answer = ""
            try:
                with requests.post(url, json={"messages": history}, stream=True) as r:
                    for chunk in r.iter_content(chunk_size=1):
                        if chunk:
                            answer += chunk.decode("utf-8")
                            placeholder.markdown(
                                f"<div style='text-align:left; margin:5px;'><span class='bot-bubble'>{answer}</span></div>",
                                unsafe_allow_html=True,
                            )
                st.session_state.messages.append(("Bot", answer))
            except Exception as e:
                st.session_state.messages.append(("Bot", f"❌ Error: {str(e)}"))

    elif mode == "Stream Knowledge Base":
        url = "http://localhost:8000/kb/stream"
        with st.spinner("📚 Searching knowledge base..."):
            placeholder = st.empty()
            answer = ""
            try:
                with requests.post(url, json={"messages": history}, stream=True) as r:
                    for chunk in r.iter_content(chunk_size=1):
                        if chunk:
                            answer += chunk.decode("utf-8")
                            placeholder.markdown(
                                f"<div style='text-align:left; margin:5px;'><span class='bot-bubble'>{answer}</span></div>",
                                unsafe_allow_html=True,
                            )
                st.session_state.messages.append(("Bot", answer))
            except Exception as e:
                st.session_state.messages.append(("Bot", f"❌ Error: {str(e)}"))
