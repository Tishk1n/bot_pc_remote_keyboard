import speech_recognition as sr
import pyttsx3
import threading
import re
import requests
from fake_useragent import UserAgent
import logging

logger = logging.getLogger(__name__)

class VoiceAssistant:
    def __init__(self, key_handler):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self.key_handler = key_handler
        self.setup_voice()
        
    def setup_voice(self):
        """Настройка голоса"""
        self.engine.setProperty('rate', 180)  # Скорость речи
        self.engine.setProperty('volume', 0.9)  # Громкость
        
        # Выбор русского женского голоса, если доступен
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "russian" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break

    def speak(self, text):
        """Озвучивание текста"""
        self.engine.say(text)
        self.engine.runAndWait()

    def search_anime(self, query):
        """Поиск аниме и озвучивание результатов"""
        try:
            headers = {
                'User-Agent': UserAgent().random,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            url = f"https://rutube.ru/api/search/video/?query={query}+аниме&format=json"
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if not data.get('results'):
                self.speak("К сожалению, ничего не найдено")
                return
            
            results = data['results'][:5]
            self.speak("Нашёл следующие видео на Рутубе:")
            
            for i, result in enumerate(results, 1):
                title = result.get('title', '').strip()
                self.speak(f"Номер {i}: {title}")
                
        except Exception as e:
            logger.error(f"Ошибка при голосовом поиске: {e}")
            self.speak("Произошла ошибка при поиске")

    def process_command(self, command):
        """Обработка голосовой команды"""
        command = command.lower()
        
        if "перемотай вперёд" in command or "вперед" in command:
            self.speak("Перематываю вперёд")
            self.key_handler(0x27)  # VK_RIGHT
            
        elif "перемотай назад" in command or "назад" in command:
            self.speak("Перематываю назад")
            self.key_handler(0x25)  # VK_LEFT
            
        elif "следующая серия" in command:
            self.speak("Включаю следующую серию")
            self.key_handler(0x4E)  # 'N'
            
        elif "предыдущая серия" in command:
            self.speak("Включаю предыдущую серию")
            self.key_handler(0x50)  # 'P'
            
        elif "найди аниме" in command:
            # Извлекаем название аниме из команды
            match = re.search(r"найди аниме\s+(.+)", command)
            if match:
                query = match.group(1)
                self.search_anime(query)
            else:
                self.speak("Пожалуйста, укажите название аниме для поиска")

    def listen(self):
        """Прослушивание микрофона"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                print("Слушаю...")
                audio = self.recognizer.listen(source)
                
                try:
                    command = self.recognizer.recognize_google(audio, language="ru-RU")
                    print(f"Распознано: {command}")
                    self.process_command(command)
                except sr.UnknownValueError:
                    pass  # Игнорируем неразборчивую речь
                except sr.RequestError as e:
                    logger.error(f"Ошибка распознавания: {e}")
                    
        except Exception as e:
            logger.error(f"Ошибка при прослушивании: {e}")

    def start_listening(self):
        """Запуск бесконечного прослушивания в отдельном потоке"""
        def listen_loop():
            while True:
                self.listen()
        
        thread = threading.Thread(target=listen_loop, daemon=True)
        thread.start()
