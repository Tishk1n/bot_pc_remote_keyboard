import speech_recognition as sr
import pyttsx3
import json
import requests
from fake_useragent import UserAgent
import logging
from speech_config import SPEECH_RECOGNITION_SETTINGS, VOICE_COMMANDS

logger = logging.getLogger(__name__)

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        # Настройка распознавания
        self.recognizer.energy_threshold = 300  # Увеличиваем чувствительность
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Уменьшаем паузу между словами
        # Настройка голоса
        self.engine.setProperty('rate', 180)
        self.engine.setProperty('volume', 0.9)

    def recognize_command(self, audio_data):
        try:
            # Увеличиваем громкость аудио
            audio_data.adjust_for_ambient_noise(audio_data)
            
            text = self.recognizer.recognize_google(
                audio_data,
                language='ru-RU',
                show_all=False  # Изменяем на False для получения строки
            )
            
            if text:
                logger.debug(f"Распознанный текст: {text}")
                return text.lower()
            return None
                
        except sr.UnknownValueError:
            logger.error("Не удалось распознать речь")
            return None
        except sr.RequestError as e:
            logger.error(f"Ошибка сервиса распознавания речи: {e}")
            return None
        except Exception as e:
            logger.error(f"Неизвестная ошибка при распознавании: {e}")
            return None

    def speak(self, text):
        try:
            rate = self.engine.getProperty('rate')
            volume = self.engine.getProperty('volume')
            
            # Сохраняем текущие настройки
            self.engine.setProperty('rate', 175)  # Немного медленнее
            self.engine.setProperty('volume', 1.0)  # Максимальная громкость
            
            self.engine.say(text)
            self.engine.runAndWait()
            
            # Восстанавливаем настройки
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
        except Exception as e:
            logger.error(f"Ошибка при озвучивании: {e}")

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
            
        # Проверяем числа для выбора варианта
        if text.strip().isdigit() or any(word in text.lower() for word in ['один', 'два', 'три', 'четыре', 'пять']):
            number_map = {
                'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
                '1': 1, '2': 2, '3': 3, '4': 4, '5': 5
            }
            for word, num in number_map.items():
                if word in text.lower():
                    return "select", num
            return "select", int(text.strip())
            
        # Проверяем команды из конфига
        for command, phrases in VOICE_COMMANDS.items():
            if any(phrase in text for phrase in phrases):
                if command == "search":
                    # Извлекаем название аниме после команды поиска
                    for phrase in phrases:
                        if phrase in text:
                            query = text.replace(phrase, "").strip()
                            return command, query
                return command, None
                
        return None, None
