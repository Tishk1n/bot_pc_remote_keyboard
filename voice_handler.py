import speech_recognition as sr
import pyttsx3
import json
import requests
from fake_useragent import UserAgent
import logging
import soundfile as sf
import numpy as np
from pydub import AudioSegment
import os
from speech_config import SPEECH_RECOGNITION_SETTINGS, VOICE_COMMANDS

logger = logging.getLogger(__name__)

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        # Оптимизированные настройки для распознавания
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 0.5
        self.recognizer.operation_timeout = None
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

    def convert_ogg_to_wav(self, ogg_path):
        """Конвертирует ogg в wav для лучшего распознавания"""
        wav_path = ogg_path.replace('.ogg', '.wav')
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format='wav')
        return wav_path

    def recognize_command(self, audio_file_path):
        try:
            # Конвертируем в WAV для лучшего распознавания
            wav_path = self.convert_ogg_to_wav(audio_file_path)
            
            with sr.AudioFile(wav_path) as source:
                # Настраиваем устранение шума
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Записываем аудио
                audio = self.recognizer.record(source)
                
                # Пробуем разные API для распознавания
                try:
                    text = self.recognizer.recognize_google(
                        audio,
                        language='ru-RU'
                    )
                    logger.info(f"Распознан текст: {text}")
                    return text.lower()
                except:
                    try:
                        # Пробуем Sphinx как запасной вариант
                        text = self.recognizer.recognize_sphinx(
                            audio,
                            language='ru-RU'
                        )
                        logger.info(f"Распознан текст (sphinx): {text}")
                        return text.lower()
                    except:
                        return None
        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            return None
        finally:
            # Очищаем временные файлы
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
            except:
                pass

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
            
        logger.info(f"Парсинг команды из текста: {text}")
        # Преобразуем текст в нижний регистр и удаляем лишние пробелы
        text = text.lower().strip()
        
        # Сначала проверяем числа
        number_words = {
            'один': 1, 'первый': 1, 'первое': 1, 'первая': 1,
            'два': 2, 'второй': 2, 'второе': 2, 'вторая': 2,
            'три': 3, 'третий': 3, 'третье': 3, 'третья': 3,
            'четыре': 4, 'четвертый': 4, 'четвертое': 4, 'четвертая': 4,
            'пять': 5, 'пятый': 5, 'пятое': 5, 'пятая': 5,
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5
        }
        
        for word, num in number_words.items():
            if word in text:
                logger.info(f"Распознан выбор номера: {num}")
                return "select", num
                
        # Проверяем команды
        for command, phrases in VOICE_COMMANDS.items():
            for phrase in phrases:
                if phrase in text:
                    if command == "search":
                        query = text.replace(phrase, "").strip()
                        logger.info(f"Распознана команда поиска: {query}")
                        return command, query
                    logger.info(f"Распознана команда: {command}")
                    return command, None
        
        logger.warning(f"Команда не распознана: {text}")
        return None, None
