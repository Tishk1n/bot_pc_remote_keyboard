import speech_recognition as sr
import pyttsx3
import json
import requests
from fake_useragent import UserAgent

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        # Настройка голоса
        self.engine.setProperty('rate', 180)  # Скорость речи
        self.engine.setProperty('volume', 0.9)  # Громкость

    def recognize_command(self, audio_data):
        try:
            text = self.recognizer.recognize_google(audio_data, language='ru-RU')
            return text.lower()
        except sr.UnknownValueError:
            return None
        except sr.RequestError:
            return None

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def search_anime(self, query):
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        url = f"https://rutube.ru/api/search/video/?query={query}+аниме&format=json"
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            results = data.get('results', [])[:3]
            
            if not results:
                self.speak("К сожалению, ничего не найдено")
                return None
            
            response_text = "Нашел следующие видео на Rutube. Скажите номер видео, которое хотите посмотреть:\n"
            for i, result in enumerate(results, 1):
                title = result.get('title', '').strip()
                response_text += f"{i}. {title}\n"
            
            self.speak(response_text)
            return results
            
        except Exception as e:
            self.speak("Произошла ошибка при поиске")
            return None

    def parse_command(self, text):
        if not text:
            return None, None
            
        # Проверяем, является ли текст числом (выбор варианта)
        if text.strip().isdigit():
            return "select", int(text.strip())
            
        if "найди аниме" in text:
            query = text.replace("найди аниме", "").strip()
            return "search", query
        elif "перемотай вперёд" in text:
            return "forward", None
        elif "перемотай назад" in text:
            return "backward", None
        elif "следующая серия" in text:
            return "next", None
        elif "предыдущая серия" in text:
            return "previous", None
        return None, None
