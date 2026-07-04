# llm_client.py
import asyncio
import google.generativeai as genai
from config import Config

# Configure the Gemini client once
genai.configure(api_key=Config.GEMINI_API_KEY)

async def ask_gemini(prompt: str) -> str:
    """
    Async wrapper for Gemini's generate_content.
    Uses asyncio.to_thread to prevent blocking the async event loop.
    """
    # Get the model
    model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    # Safety settings (optional but recommended for RPG violence)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    
    # Run the synchronous call in a separate thread
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
        None,  # Uses default ThreadPoolExecutor
        lambda: model.generate_content(
            prompt,
            safety_settings=safety_settings,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=800,
            )
        )
    )
    
    # Handle potential block
    if not response.text:
        return "The Dungeon Master remained silent (content blocked). Please rephrase your action."
    
    return response.text