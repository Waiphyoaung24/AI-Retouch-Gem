from google import genai
from google.genai import types
from PIL import Image
import io
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("WARNING: GOOGLE_API_KEY not set in environment.")

client = genai.Client(api_key=api_key)

import asyncio

async def try_on_jewellery(
    jewellery_image_bytes: bytes,
    hand_model_image_bytes: bytes,
    prompt: str,
) -> bytes:
    try:
        jewellery_img = Image.open(io.BytesIO(jewellery_image_bytes))
        hand_img = Image.open(io.BytesIO(hand_model_image_bytes))

        def _call_gemini():
            return client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[prompt, jewellery_img, hand_img],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )

        response = await asyncio.to_thread(_call_gemini)

        for part in response.parts:
            if part.inline_data is not None:
                return part.inline_data.data

        raise ValueError("Gemini did not return an image")

    except Exception as e:
        print(f"Gemini API Error: {e}")
        raise e
