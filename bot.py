import io
import os
import telebot
from telebot import types
from googletrans import Translator
import speech_recognition as sr
from tempfile import NamedTemporaryFile
from pydub import AudioSegment
from pydub.playback import play

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

# Создаем клавиатуру
main_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
main_keyboard.add(types.KeyboardButton("Start Translate"))

languages_keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
languages = [
    "English 🇺🇸", "Russian 🇷🇺", "Polish 🇵🇱",
    "Spanish 🇪🇸", "French 🇫🇷", "German 🇩🇪",
    "Italian 🇮🇹", "Portuguese 🇵🇹", "Dutch 🇳🇱",
    "Swedish 🇸🇪", "Norwegian 🇳🇴", "Danish 🇩🇰",
    "Finnish 🇫🇮", "Greek 🇬🇷", "Czech 🇨🇿",
    "Hungarian 🇭🇺", "Romanian 🇷🇴", "Bulgarian 🇧🇬",
    "Chinese 🇨🇳", "Japanese 🇯🇵", "Korean 🇰🇷",
    "Arabic 🇸🇦", "Turkish 🇹🇷", "Hindi 🇮🇳",
    "Ukrainian 🇺🇦"
]
languages_keyboard.add(*[types.KeyboardButton(language) for language in languages])

# Переменные для хранения выбранного языка и текста для перевода
selected_communication_language = ""
selected_translation_language = ""
text_to_translate = ""

def send_message(message, text, reply_markup=None):
    bot.reply_to(message, text, reply_markup=reply_markup)

def select_communication_language(message, language_code, language_name):
    global selected_communication_language
    selected_communication_language = language_code
    send_message(message, f"Great! Now, select the language to which you want to translate your voice. You have chosen to communicate in {selected_communication_language}.", reply_markup=languages_keyboard)

def select_translation_language(message, language_code, language_name):
    global selected_translation_language
    selected_translation_language = language_code
    send_message(message, f"Okay, now please send me the voice which you want to translate. Voice will be translated to this language: {selected_translation_language}.", reply_markup=languages_keyboard)

# Обработчики для команд /start и /hello
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    send_message(message, "Choose an option:", reply_markup=main_keyboard)

# Обработчики для кнопки Start Translate
@bot.message_handler(func=lambda message: message.text == "Start Translate")
def start_translate(message):
    global selected_communication_language, selected_translation_language
    selected_communication_language = ""
    selected_translation_language = ""
    send_message(message, "Select the language in which you want to communicate:", reply_markup=languages_keyboard)

# Обработчики для кнопок с выбором языка общения
@bot.message_handler(func=lambda message: message.text in languages)
def select_language_handler(message):
    global selected_communication_language, selected_translation_language, text_to_translate

    language_mapping = {
        "English 🇺🇸": "en",
        "Russian 🇷🇺": "ru",
        "Polish 🇵🇱": "pl",
        "Spanish 🇪🇸": "es",
        "French 🇫🇷": "fr",
        "German 🇩🇪": "de",
        "Italian 🇮🇹": "it",
        "Portuguese 🇵🇹": "pt",
        "Dutch 🇳🇱": "nl",
        "Swedish 🇸🇪": "sv",
        "Norwegian 🇳🇴": "no",
        "Danish 🇩🇰": "da",
        "Finnish 🇫🇮": "fi",
        "Greek 🇬🇷": "el",
        "Czech 🇨🇿": "cs",
        "Hungarian 🇭🇺": "hu",
        "Romanian 🇷🇴": "ro",
        "Bulgarian 🇧🇬": "bg",
        "Chinese 🇨🇳": "zh",
        "Japanese 🇯🇵": "ja",
        "Korean 🇰🇷": "ko",
        "Arabic 🇸🇦": "ar",
        "Turkish 🇹🇷": "tr",
        "Hindi 🇮🇳": "hi",
        "Ukrainian 🇺🇦": "uk"
    }
    language_name = message.text

    if language_name == "Back":
        selected_communication_language = ""
        selected_translation_language = ""
        text_to_translate = ""
        send_welcome(message)
        return

    language_code = language_mapping.get(language_name)

    if language_code:
        if not selected_communication_language:
            select_communication_language(message, language_code, language_name)
        elif not selected_translation_language:
            select_translation_language(message, language_code, language_name)

# Обработчик для голосовых сообщений
@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    global text_to_translate

    if not selected_communication_language or not selected_translation_language:
        send_message(message, "Please select both communication and translation languages first.", reply_markup=languages_keyboard)
        return

    voice_file_id = message.voice.file_id
    voice_file_info = bot.get_file(voice_file_id)
    voice_file = bot.download_file(voice_file_info.file_path)

    # Конвертация OGG в WAV
    audio_segment = AudioSegment.from_file(io.BytesIO(voice_file), format="ogg")
    wav_data = io.BytesIO()
    audio_segment.export(wav_data, format="wav")
    wav_data.seek(0)

    recognizer = sr.Recognizer()

    # Создаем временный файл для сохранения голосового сообщения
    with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(wav_data.read())

    with sr.AudioFile(temp_file.name) as audio_file:
        audio_data = recognizer.record(audio_file)

        try:
            # Распознаем речь
            text_to_translate = recognizer.recognize_google(audio_data, language=selected_communication_language)
            bot.reply_to(message, f"Recognized text: {text_to_translate}")

            # Переводим текст
            translator = Translator()
            translated_text = translator.translate(text_to_translate, dest=selected_translation_language).text
            bot.reply_to(message, f"Translated text: {translated_text}")

        except sr.UnknownValueError:
            bot.reply_to(message, "Sorry, could not understand the audio.")
        except sr.RequestError as e:
            bot.reply_to(message, f"Error during recognition: {e}")

    # Удаляем временный файл
    os.remove(temp_file.name)

    # Возвращаем пользователя в главное меню
    send_welcome(message)

# Запуск бота
bot.infinity_polling()
