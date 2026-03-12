from googletrans import Translator

translator = Translator()

def translate_to_english(text: str) -> str:
    if not text:
        return text
    try:
        result = translator.translate(text, src="es", dest="en")
        return result.text
    except Exception:
        return text
