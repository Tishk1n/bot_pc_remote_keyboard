import pyautogui
import time
from utils.logger import log

class PlayerControl:
    def __init__(self):
        # Защита от слишком быстрого выполнения команд
        pyautogui.PAUSE = 0.3
        
    def pause(self):
        """Приостановить воспроизведение"""
        try:
            pyautogui.press('space')
            log("Воспроизведение приостановлено")
        except Exception as e:
            log(f"Ошибка при попытке паузы: {e}", level="error")

    def play(self):
        """Продолжить воспроизведение"""
        try:
            pyautogui.press('k')
            log("Воспроизведение продолжено")
        except Exception as e:
            log(f"Ошибка при попытке воспроизведения: {e}", level="error")

    def seek(self, seconds):
        """Перемотка вперед/назад"""
        try:
            key = 'right' if seconds > 0 else 'left'
            times = abs(seconds) // 10
            for _ in range(times):
                pyautogui.press(key)
                time.sleep(0.1)
            log(f"Перемотка {'вперед' if seconds > 0 else 'назад'} на {seconds} секунд")
        except Exception as e:
            log(f"Ошибка при перемотке: {e}", level="error")

    def previous_episode(self):
        """Переход к предыдущему видео"""
        try:
            pyautogui.hotkey('shift', 'p')
            log("Переход к предыдущей серии")
        except Exception as e:
            log(f"Ошибка при переходе к предыдущей серии: {e}", level="error")

    def next_episode(self):
        """Переход к следующему видео"""
        try:
            pyautogui.hotkey('shift', 'n')
            log("Переход к следующей серии")
        except Exception as e:
            log(f"Ошибка при переходе к следующей серии: {e}", level="error")

    def set_speed(self, increase=True):
        """Изменение скорости воспроизведения"""
        try:
            pyautogui.press('>' if increase else '<')
            log(f"Скорость воспроизведения {'увеличена' if increase else 'уменьшена'}")
        except Exception as e:
            log(f"Ошибка при изменении скорости: {e}", level="error")

    def jump_to_percent(self, percent):
        """Переход к определенному моменту видео"""
        if 0 <= percent <= 9:
            try:
                pyautogui.press(str(percent))
                log(f"Переход к {percent}0% видео")
            except Exception as e:
                log(f"Ошибка при переходе к позиции: {e}", level="error")