# run_game.py
import os
from dotenv import load_dotenv

load_dotenv()

import asyncio

os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
os.environ["COGNEE_LLM_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"

from dungeon_master import DungeonMaster
from llm_client import ask_gemini

async def main():
    dm = DungeonMaster("The Lost Relic")

    # Seed the world (same as before)
    await dm.remember("The kingdom of Eldoria is threatened by the Shadow Cult.")
    await dm.remember("The Lost Relic of Aethel is hidden somewhere in the Forbidden Forest.")
    await dm.remember_character("Thorn", "A grizzled ranger who knows the forest's secrets but trusts no one.")
    await dm.remember_location("Forbidden Forest", "A dense, magical woodland where the trees whisper warnings.")
    await dm.remember_item("Map of Eldoria", "An old parchment showing the forest's hidden paths.", "Thorn's pack")

    print("🎲 Welcome to the AI Dungeon Master (Powered by Gemini 1.5 Pro)!")
    print("Type your actions (e.g., 'I approach the ranger and ask about the relic')")
    print("Type 'quit' to exit.\n")

    action_count = 0

    while True:
        player_action = input("> What do you do? ")
        if player_action.lower() in ["quit", "exit"]:
            break

        # Pass the Gemini function here
        response = await dm.generate_response(player_action, ask_gemini) 
        print(f"\n🎭 {response}\n")

        await dm.remember_decision("Player", player_action, response)

        action_count += 1
        if action_count % 5 == 0:
            print("🔄 The DM is refining the story world...")
            await dm.improve()
            print("✅ Story consistency enhanced!")

    await dm.improve()
    print("Thanks for playing! The world remembers your deeds.")

if __name__ == "__main__":
    asyncio.run(main())