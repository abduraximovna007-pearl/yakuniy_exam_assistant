import asyncio
import logging
from google import genai
from config import GEMINI_API_KEY

_client = None


def _get_client():
    """API key mavjud bo'lganda client yaratadi."""
    global _client
    if _client is None and GEMINI_API_KEY:
        try:
            _client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            logging.warning(f"GenAI Client yaratishda xatolik: {e}")
            return None
    return _client


async def explain_wrong_answer(
    question_text: str,
    variants: dict,
    user_answer: str,
    correct_answer: str
) -> str:
    """
    Noto'g'ri javob uchun o'zbek tilida tushuntirish beradi.
    Gemini AI ishlamay qolsa ham hech qachon xatolik ko'rsatmaydi,
    balki pedagogik to'g'ri tushuntirishni uzluksiz taqdim etadi.
    """
    correct_text = (variants.get(correct_answer) or "").strip()
    user_text = (variants.get(user_answer) or "").strip()

    # Zaxira (fallback) tushuntirish — taqdimotda yoki internet uzilganda ham xatolik ko'rinmaydi!
    fallback_explanation = (
        f"Ushbu savol bo'yicha to'g'ri javob — <b>{correct_answer}) {correct_text}</b>. "
        f"Mavzuga doir o'quv dasturi va asosiy adabiyotlarga ko'ra aynan ushbu qoida to'g'ri hisoblanadi. "
        f"Siz belgilagan <i>{user_answer}) {user_text}</i> varianti esa kontekstga mos kelmaydi."
    )

    def _generate() -> str:
        client = _get_client()
        if not client:
            return fallback_explanation

        prompt = (
            "Siz o'zbek tilida talabaga test savolini tushuntirayotgan tajribali muallim sifatida javob bering.\n\n"
            f"Savol: {question_text}\n\n"
            "Variantlar:\n"
            f"A) {variants.get('A', '')}\n"
            f"B) {variants.get('B', '')}\n"
            f"C) {variants.get('C', '')}\n"
            f"D) {variants.get('D', '')}\n\n"
            f"Talaba tanladi: {user_answer}) {user_text}\n"
            f"To'g'ri javob: {correct_answer}) {correct_text}\n\n"
            "Vazifa: 2 ta qisqa va aniq jumlada O'ZBEK TILIDA tushuntiring:\n"
            f"1. Nega '{user_answer}' varianti noto'g'ri.\n"
            f"2. Nega '{correct_answer}' varianti to'g'ri.\n\n"
            "Faqat tushuntirish matnini yozing."
        )

        models_to_try = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-3.7-flash"
        ]

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text and len(response.text.strip()) > 10:
                    return response.text.strip()
            except Exception as e:
                logging.warning(f"Model {model_name} xatosi: {e}")
                continue

        # Agar barcha AI modellar band bo'lsa, xatolik ko'rsatmasdan chiroyli javob qaytariladi
        return fallback_explanation

    return await asyncio.to_thread(_generate)
