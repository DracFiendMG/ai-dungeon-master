# streamlit_app.py
import streamlit as st
import asyncio
from dungeon_master import DungeonMaster
from llm_client import ask_gemini  # <--- Changed here

@st.cache_resource
def get_dm():
    dm = DungeonMaster("Streamlit Campaign")
    # Seed once (async inside sync context - using asyncio.run)
    asyncio.run(dm.remember("The kingdom of Eldoria is threatened by the Shadow Cult."))
    asyncio.run(dm.remember("The Lost Relic of Aethel is hidden somewhere in the Forbidden Forest."))
    asyncio.run(dm.remember_character("Thorn", "A grizzled ranger who knows the forest's secrets."))
    return dm

dm = get_dm()

st.set_page_config(page_title="AI Dungeon Master", page_icon="🎲")
st.title("🎲 AI Dungeon Master with Gemini Memory")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Welcome, adventurer! The world of Eldoria awaits. What do you do?"}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("What do you do?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("The DM is consulting the ancient scrolls (Gemini)..."):
            context_list = asyncio.run(dm.recall(prompt))
            context = "\n".join(context_list)
            full_prompt = f"""
            You are a Dungeon Master for a fantasy RPG.
            ESTABLISHED FACTS:
            {context}
            PLAYER ACTION:
            {prompt}
            Respond as the DM. Describe the outcome and provide options.
            """
            # Use Gemini here
            response = asyncio.run(ask_gemini(full_prompt))
            st.write(response)
    
    asyncio.run(dm.remember_decision("Player", prompt, response))
    st.session_state.messages.append({"role": "assistant", "content": response})

    if len(st.session_state.messages) % 10 == 0:
        with st.spinner("The DM is weaving the threads of fate..."):
            asyncio.run(dm.improve())
        st.success("World memory consolidated!")