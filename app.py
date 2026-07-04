import streamlit as st
import asyncio
import cognee
import google.generativeai as genai
import os
from dotenv import load_dotenv
from config import Config

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def configure_cognee() -> None:
    api_key = Config.GEMINI_API_KEY
    os.environ["GOOGLE_API_KEY"] = api_key
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["COGNEE_LLM_API_KEY"] = api_key

    cognee.config.set_llm_provider("gemini")
    cognee.config.set_llm_model(f"gemini/{Config.GEMINI_MODEL}")
    cognee.config.set_llm_api_key(api_key)
    cognee.config.set_embedding_config(
        {
            "embedding_provider": Config.COGNEE_EMBEDDING_PROVIDER,
            "embedding_model": Config.COGNEE_EMBEDDING_MODEL,
        }
    )


configure_cognee()

# ---------- cognee setup ----------
DATASET_NAME = "dnd_campaign"

async def add_to_memory(user_text, dm_text):
    content = f"Player: {user_text}\nDungeon Master: {dm_text}"
    await cognee.add(content, dataset_name=DATASET_NAME)
    await cognee.cognify()

async def search_memory(query, k=3):
    results = await cognee.search(query, dataset_name=DATASET_NAME)
    snippets = []
    for r in results[:k]:
        if hasattr(r, 'text'):
            snippets.append(r.text)
        elif isinstance(r, dict) and 'text' in r:
            snippets.append(r['text'])
    return "\n".join(snippets) if snippets else "No relevant history."

# Seed world lore once
if "world_seeded" not in st.session_state:
    async def seed_world():
        await cognee.add(
            "The world of Thalassia is a medieval realm. The capital city is Stormhold. "
            "A dark wizard named Malachar seeks the Crystal of Eternity. "
            "The player starts in the village of Oakvale.",
            dataset_name=DATASET_NAME
        )
        await cognee.cognify()
    asyncio.run(seed_world())
    st.session_state.world_seeded = True

# ---------- UI ----------
st.title("🐉 AI Dungeon Master with Memory (Gemini)")
st.caption("Every choice is remembered.")

# Sidebar
with st.sidebar:
    st.header("Character Sheet")
    char_name = st.text_input("Name", "Arin")
    char_class = st.selectbox("Class", ["Warrior", "Mage", "Rogue"])
    if st.button("Save Character"):
        async def save_char():
            await cognee.add(
                f"Player character: {char_name}, a {char_class}.", DATASET_NAME
            )
            await cognee.cognify()
        asyncio.run(save_char())
        st.success("Character saved!")
    if st.button("New Campaign"):
        async def reset():
            await cognee.prune.prune_data()
        asyncio.run(reset())
        st.session_state.messages = []
        st.rerun()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
user_input = st.chat_input("What do you do?")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)

    # Retrieve memory
    memory_context = asyncio.run(search_memory(user_input))

    # System instruction with memory
    system_instruction = f"""You are a creative Dungeon Master running a fantasy campaign.
Current player character: {char_name} the {char_class}.
Relevant campaign history:
{memory_context}
---
Use the history to maintain continuity. Be imaginative and descriptive.
Keep responses under 250 words. Stay in character."""

    # Set up model with recent conversation
    model = genai.GenerativeModel(
        "models/gemini-2.5-flash",
        system_instruction=system_instruction
    )
    recent_history = [
        {"role": m["role"], "parts": [m["content"]]}
        for m in st.session_state.messages[-10:] if m["role"] in ("user", "assistant")
    ]
    chat = model.start_chat(history=recent_history)

    # Generate response
    response = chat.send_message(user_input)
    dm_text = response.text

    st.session_state.messages.append({"role": "assistant", "content": dm_text})
    st.chat_message("assistant").write(dm_text)

    # Store in cognee
    asyncio.run(add_to_memory(user_input, dm_text))

    # Show memory panel
    with st.expander("🧠 DM's Recollection"):
        recent_mem = asyncio.run(search_memory("recent events", k=2))
        st.text(recent_mem)