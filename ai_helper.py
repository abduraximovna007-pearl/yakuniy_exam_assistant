import asyncio
from google import genai
from config import GEMINI_API_KEY

# Lazy initialization — client only created when first used
_client = None


def _get_client() -> genai.Client:
    """API key mavjud bo'lganda client yaratadi."""
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY topilmadi. .env fayliga GEMINI_API_KEY qo'shing.\n"
                "Kalit olish: https://aistudio.google.com/app/apikey"
            )
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


async def explain_wrong_answer(
    question_text: str,
    variants: dict,
    user_answer: str,
    correct_answer: str
) -> str:
    """
    Gemini AI orqali noto'g'ri javob uchun o'zbek tilida tushuntirish oladi.
    """
    def _generate() -> str:
        prompt = (
            "Siz o'zbek tilida talabaga test savolini tushuntirayotgan muallim sifatida javob bering.\n\n"
            f"Savol: {question_text}\n\n"
            "Variantlar:\n"
            f"A) {variants.get('A', '')}\n"
            f"B) {variants.get('B', '')}\n"
            f"C) {variants.get('C', '')}\n"
            f"D) {variants.get('D', '')}\n\n"
            f"Talaba tanladi: {user_answer}) {variants.get(user_answer, '')}\n"
            f"To'g'ri javob: {correct_answer}) {variants.get(correct_answer, '')}\n\n"
            "Iltimos, 2-3 jumlada O'ZBEK TILIDA qisqa va tushunarli tushuntiring:\n"
            f"1. Nima uchun '{user_answer}' varianti xato\n"
            f"2. Nima uchun '{correct_answer}' varianti to'g'ri\n\n"
            "Faqat tushuntirishni yozing, boshqa hech narsa qo'shmang."
        )
        
        # Google API da yuklama bo'lganda navbat bilan tekshirish uchun modellar
        models_to_try = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-3.7-flash"
        ]
        
        for model_name in models_to_try:
            try:
                client = _get_client()
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text.strip()
            except ValueError as e:
                return f"AI sozlanmagan: {str(e)[:80]}"
            except Exception:
                # Agar ushbu modelda yuklama (503) yoki xatolik bo'lsa, keyingi modelga o'tadi
                continue

        return "AI tushuntirish berishda vaqtincha xatolik yuz berdi."

    return await asyncio.to_thread(_generate)
