# filepath: /anime-voice-assistant/anime-voice-assistant/src/main.py

import speech_recognition as sr
from voice.recognizer import VoiceRecognizer
from voice.noise_reduction import reduce_noise
from rutube.api import RutubeAPI
from rutube.player_control import PlayerControl
from browser.controller import BrowserController
from utils.logger import log

class AnimeVoiceAssistant:
    def __init__(self):
        try:
            self.recognizer = VoiceRecognizer()
        except AttributeError as e:
            log("Ошибка инициализации VoiceRecognizer: " + str(e), level="error")
            log("Проверьте, установлен ли пакет pyaudio: pip install pyaudio", level="error")
            raise SystemExit(1)
        self.rutube_api = RutubeAPI()
        self.player_control = PlayerControl()
        self.browser = BrowserController()

    def process_command(self, command):
        if not command:
            return
            
        log(f"Получена команда: {command}")
        command = command.lower().strip()
        
        # Словарь команд для лучшего распознавания
        commands = {
            "пауза": ["пауза", "стоп", "остановить"],
            "продолжить": ["продолжить", "плей", "играть", "старт"],
            "вперед": ["вперед", "перемотать вперед"],
            "назад": ["назад", "перемотать назад"],
            "следующая": ["следующая серия", "следующий", "дальше"],
            "предыдущая": ["предыдущая серия", "предыдущий", "назад"],
            "поиск": ["найти", "поиск", "найди", "искать"]
        }
        
        for action, variants in commands.items():
            if any(variant in command for variant in variants):
                log(f"Выполняется команда: {action}")
                if action == "пауза":
                    self.player_control.pause()
                elif action == "продолжить":
                    self.player_control.play()
                elif action == "вперед":
                    self.player_control.seek(10)
                elif action == "назад":
                    self.player_control.seek(-10)
                elif action == "следующая":
                    self.player_control.next_episode()
                elif action == "предыдущая":
                    self.player_control.previous_episode()
                elif action == "поиск":
                    title = command.split("найти")[-1].strip()
                    if not title:
                        title = command.split("поиск")[-1].strip()
                    self.search_anime(title)
                return
        
        log("Неизвестная команда")

    def search_anime(self, title):
        log(f"Поиск аниме: {title}")
        results = self.rutube_api.search_anime(title)
        if not results:
            log("Ничего не найдено")
            return
        
        for index, anime in enumerate(results):
            log(f"{index + 1}: {anime['title']} ({anime['description'][:100]}...)")
        
        # Открываем первый найденный результат в браузере
        if results:
            video_info = self.rutube_api.get_video_info(results[0]['id'])
            if video_info and 'video_url' in video_info:
                self.browser.open_url(video_info['video_url'])

    def run(self):
        log("Anime Voice Assistant is starting...")
        while True:
            audio = self.recognizer.listen()
            command = self.recognizer.recognize(audio)
            if command:
                self.process_command(command)

if __name__ == "__main__":
    assistant = AnimeVoiceAssistant()
    assistant.run()