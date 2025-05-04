import speech_recognition as sr
import numpy as np
from voice.noise_reduction import reduce_noise
from speech_recognition import AudioData

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Настройка параметров распознавания
        self.recognizer.energy_threshold = 4000  # Увеличиваем порог энергии
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Увеличиваем паузу между фразами
        self.recognizer.phrase_threshold = 0.3  # Минимальная длина фразы

    def listen(self):
        with self.microphone as source:
            print("Настройка уровня шума...")
            # Увеличиваем время калибровки для лучшей настройки
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Слушаю...")
            try:
                # Увеличиваем timeout для лучшего распознавания
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                return audio
            except Exception as e:
                print(f"Ошибка при прослушивании: {e}")
                return None

    def recognize(self, audio):
        if not audio:
            return None
            
        try:
            # Пробуем разные варианты распознавания
            try:
                command = self.recognizer.recognize_google(audio, language='ru-RU')
            except:
                # Пробуем без указания языка
                command = self.recognizer.recognize_google(audio)
                
            print(f"Распознана команда: {command}")
            return command.lower()  # Приводим к нижнему регистру для единообразия
            
        except sr.UnknownValueError:
            print("Не удалось распознать речь")
            return None
        except sr.RequestError as e:
            print(f"Ошибка сервиса распознавания речи: {e}")
            return None

    def process_command(self):
        audio = self.listen()
        command = self.recognize(audio)
        return command