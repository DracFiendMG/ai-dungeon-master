# dungeon_master.py
import re
import cognee
from config import Config
from typing import Optional, List
from uuid import UUID

import os
from dotenv import load_dotenv
load_dotenv()

class DungeonMaster:
    def __init__(self, campaign_name: str = "default_campaign"):
        self.campaign = campaign_name
        # Sanitize: replace any non-alphanumeric with '_'
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', campaign_name)
        self.dataset = f"campaign_{safe_name}"
        self.llm_provider = Config.DEFAULT_LLM
        self._setup_cognee()

    def _setup_cognee(self):
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing; Cognee cannot initialize.")

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

    # ----------- MEMORY OPERATIONS -----------

    async def remember(self, text: str):
        """Store a piece of narrative into the memory graph."""
        await cognee.remember(
            text,
            dataset_name=self.dataset
        )

    async def recall(self, query: str, top_k: int = 5) -> List[str]:
        """Query the memory graph and return relevant facts as strings."""
        results = await cognee.recall(
            query_text=query,
            dataset_name=self.dataset,
            top_k=top_k
        )
        return [r.text for r in results]

    async def improve(self):
        """Run the memify process to enrich the graph."""
        await cognee.improve(dataset=self.dataset)

    async def forget(self, query: str):
        """Remove specific memory entries."""
        try:
            results = await cognee.search(query, dataset_name=self.dataset)
        except Exception:
            results = []

        data_ids = []
        for result in results:
            metadata = getattr(result, "metadata", None)
            if isinstance(metadata, dict):
                data_id = metadata.get("data_id")
                if data_id:
                    data_ids.append(str(data_id))
                    continue
            if isinstance(result, dict):
                metadata = result.get("metadata", {})
                if isinstance(metadata, dict) and metadata.get("data_id"):
                    data_ids.append(str(metadata["data_id"]))

        if not data_ids:
            await cognee.forget(dataset=self.dataset, memory_only=True)
            return

        for data_id in dict.fromkeys(data_ids):
            await cognee.forget(
                data_id=UUID(data_id),
                dataset=self.dataset,
                memory_only=True,
            )

    # ----------- DOMAIN HELPERS -----------

    async def remember_character(self, name: str, description: str):
        await self.remember(f"CHARACTER: {name} - {description}")

    async def remember_location(self, name: str, description: str):
        await self.remember(f"LOCATION: {name} - {description}")

    async def remember_item(self, name: str, description: str, location: str = None):
        text = f"ITEM: {name} - {description}"
        if location:
            text += f" (located at {location})"
        await self.remember(text)

    async def remember_decision(self, player: str, action: str, consequence: str):
        await self.remember(
            f"DECISION: {player} chose '{action}' which led to {consequence}"
        )

    async def get_character_info(self, name: str) -> str:
        results = await self.recall(f"Tell me about character {name}")
        return "\n".join(results) if results else f"No information about {name}."

    async def get_world_context(self, query: str) -> str:
        results = await self.recall(query, top_k=5)
        return "\n".join(results)

    async def check_consistency(self, proposed_event: str) -> bool:
        results = await self.recall(f"Contradictions to: {proposed_event}")
        for r in results:
            if any(word in r.lower() for word in ["not", "never", "contradict"]):
                return False
        return True

    async def generate_response(self, player_action: str, llm_func) -> str:
        context_list = await self.recall(player_action, top_k=5)
        context = "\n".join(context_list)
        prompt = f"""
You are a Dungeon Master for a fantasy RPG.
Use the following established world facts to stay consistent.

ESTABLISHED FACTS:
{context}

PLAYER ACTION:
{player_action}

Now respond as the DM. Describe the outcome vividly and then provide 2-3 clear options for the player.
"""
        response = await llm_func(prompt)
        return response

    async def reset_campaign(self):
        await cognee.forget(dataset=self.dataset, memory_only=True)