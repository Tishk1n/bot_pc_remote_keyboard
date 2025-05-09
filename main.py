from aiogram import Bot, Dispatcher, types, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import os
import asyncio
from config import TOKEN
import requests
from bs4 import BeautifulSoup
import webbrowser
from aiogram.utils.markdown import hbold, hitalic
from database import Database
import subprocess
import win32gui
import win32con
import win32api
from fake_useragent import UserAgent
import logging
from ctypes import Structure, c_ulong, c_ushort, c_short, POINTER, windll, Union, c_void_p, sizeof, c_long, byref, pointer
import time
from voice_handler import VoiceHandler
import speech_recognition as sr

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Инициализация базы данных
db = Database()

# Создание клавиатур
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎌 Аниме")],
        [KeyboardButton(text="⚡️ Выключить компьютер")]
    ],
    resize_keyboard=True
)

anime_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏸ Пауза/Продолжить")],
        [KeyboardButton(text="⏩ Вперед 10 сек"), KeyboardButton(text="⏪ Назад 10 сек")],
        [KeyboardButton(text="⬅️ Предыдущая серия"), KeyboardButton(text="➡️ Следующая серия")],
        [KeyboardButton(text="🔍 Поиск аниме")]
    ],
    resize_keyboard=True
)

class SearchStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_choice = State()  # Новое состояние для ожидания выбора

# Добавим словарь для хранения результатов поиска
search_results = {}

# Обработчик команды /start
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    db.log_user(message.from_user.id, message.from_user.username)
    stats = db.get_statistics()
    
    welcome_text = (
        f"🎉 {hbold('Добро пожаловать в Anime Control Bot!')}\n\n"
        f"📊 {hbold('Статистика бота:')}\n"
        f"👥 Всего пользователей: {hitalic(stats['total_users'])}\n"
        f"🎯 Выполнено команд: {hitalic(stats['total_commands'])}\n"
        f"🎬 Просмотрено аниме: {hitalic(stats['total_anime'])}\n\n"
        f"🏆 {hbold('Топ-3 популярных аниме:')}\n"
    )
    
    if stats['top_anime']:
        for title, count in stats['top_anime']:
            welcome_text += f"• {title}: {count} просмотров\n"
    
    await message.answer(welcome_text, reply_markup=main_kb, parse_mode="HTML")
    db.log_command(message.from_user.id, "start")

# Обработчик кнопки "Аниме"
@dp.message(F.text == "🎌 Аниме")
async def anime_menu(message: types.Message):
    db.log_command(message.from_user.id, "anime_menu")
    await message.answer(
        f"🎮 {hbold('Управление аниме:')}\n"
        f"Используйте кнопки для управления воспроизведением",
        reply_markup=anime_kb,
        parse_mode="HTML"
    )

# Обработчик кнопки "Выключить компьютер"
@dp.message(F.text == "⚡️ Выключить компьютер")
async def shutdown_pc(message: types.Message):
    db.log_command(message.from_user.id, "shutdown")
    subprocess.run(["shutdown", "/s", "/t", "10", "/c", "Компьютер будет выключен через 10 секунд"])
    await message.answer("⚠️ Компьютер будет выключен через 10 секунд")

def find_browser_window():
    """Поиск и активация окна браузера"""
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            if 'chrome' in title or 'firefox' in title or 'edge' in title:
                windows.append(hwnd)
        return True
    
    windows = []
    win32gui.EnumWindows(callback, windows)
    if windows:
        win32gui.SetForegroundWindow(windows[0])
        return True
    return False

def send_key(key):
    """Отправка нажатия клавиши в активное окно"""
    if find_browser_window():
        if isinstance(key, str):
            win32api.keybd_event(ord(key.upper()), 0, 0, 0)
            win32api.keybd_event(ord(key.upper()), 0, win32con.KEYEVENTF_KEYUP, 0)
        else:
            win32api.keybd_event(key, 0, 0, 0)
            win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)

# Исправляем определение структур
class MOUSEINPUT(Structure):
    _fields_ = (
        ("dx", c_long),
        ("dy", c_long),
        ("mouseData", c_ulong),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", c_void_p)
    )

class KEYBDINPUT(Structure):
    _fields_ = (
        ("wVk", c_ushort),
        ("wScan", c_ushort),
        ("dwFlags", c_ulong),
        ("time", c_ulong),
        ("dwExtraInfo", c_void_p)
    )

class HARDWAREINPUT(Structure):
    _fields_ = (
        ("uMsg", c_ulong),
        ("wParamL", c_short),
        ("wParamH", c_ushort)
    )

class INPUT_UNION(Union):
    _fields_ = (
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    )

class INPUT(Structure):
    _fields_ = (
        ("type", c_ulong),
        ("union", INPUT_UNION),
    )

def send_media_key(key_code):
    """Отправка клавиш в медиаплеер"""
    try:
        # Находим окно браузера
        hwnd = win32gui.FindWindow(None, "Rutube")
        if not hwnd:
            # Если не нашли по имени Rutube, ищем по содержимому заголовка
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if 'rutube' in title:
                        windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(callback, windows)
            if windows:
                hwnd = windows[0]
        
        if hwnd:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.1)  # Даем окну время стать активным
            
            # Отправляем виртуальный код клавиши
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, key_code, 0)
            time.sleep(0.05)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, key_code, 0)
            return True
    except Exception as e:
        logger.error(f"Ошибка при отправке медиа-клавиши: {e}")
    return False

# Обновляем обработчики кнопок
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def find_video_window():
    """Поиск окна с видео"""
    try:
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    title = win32gui.GetWindowText(hwnd).lower()
                    # Расширяем список поисковых терминов
                    search_terms = ['rutube', 'chrome', 'firefox', 'edge', 'смотреть', 
                                 'видео', 'video', 'anime', 'аниме', 'серия', 'episode']
                    if any(x in title for x in search_terms):
                        windows.append(hwnd)
                except Exception:
                    pass
            return True
        
        windows = []
        win32gui.EnumWindows(callback, windows)
        
        # Если нашли окна, возвращаем первое активное
        for hwnd in windows:
            if win32gui.IsWindowVisible(hwnd):
                return hwnd
                
        # Пробуем найти по классу окна
        hwnd = win32gui.FindWindow("Chrome_WidgetWin_1", None)
        if hwnd and win32gui.IsWindowVisible(hwnd):
            return hwnd
            
        return None
        
    except Exception as e:
        logger.error(f"Ошибка при поиске окна: {e}")
        return None

def send_input_key(vk_code):
    """Отправка клавиши через SendInput с учетом скан-кода"""
    try:
        hwnd = find_video_window()
        if not hwnd:
            logger.error("Не удалось найти окно видео")
            return False
            
        try:
            # Активируем окно
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Пробуем активировать окно всеми способами
            try:
                win32gui.SetForegroundWindow(hwnd)
            except:
                try:
                    win32gui.BringWindowToTop(hwnd)
                    win32gui.SetFocus(hwnd)
                except:
                    pass
            
            time.sleep(0.3)  # Увеличиваем задержку
            
            # 1. Отправляем через keybd_event с скан-кодом
            scan_code = win32api.MapVirtualKey(vk_code, 0)
            win32api.keybd_event(vk_code, scan_code, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(vk_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)
            
            # 2. Отправляем через PostMessage с lparam
            lparam = (scan_code << 16) | 1
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, lparam)
            time.sleep(0.1)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, lparam | (1 << 30))
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка отправки клавиши: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка общая: {e}")
        return False

# Обновляем обработчики кнопок управления с правильными кодами клавиш
@dp.message(F.text == "⏸ Пауза/Продолжить")
async def toggle_pause(message: types.Message):
    if send_input_key(win32con.VK_SPACE):  # Пробел
        await message.answer("⏸ Переключение паузы")
    else:
        await message.answer("❌ Не удалось найти окно с видео")

@dp.message(F.text == "⏩ Вперед 10 сек")
async def forward_10(message: types.Message):
    if send_input_key(win32con.VK_RIGHT):  # Стрелка вправо
        await message.answer("⏩ Перемотка вперед")
    else:
        await message.answer("❌ Не удалось найти окно с видео")

@dp.message(F.text == "⏪ Назад 10 сек")
async def backward_10(message: types.Message):
    if send_input_key(win32con.VK_LEFT):  # Стрелка влево
        await message.answer("⏪ Перемотка назад")
    else:
        await message.answer("❌ Не удалось найти окно с видео")

@dp.message(F.text == "⬅️ Предыдущая серия")
async def previous_episode(message: types.Message):
    if send_input_key(ord('P')):  # Клавиша P
        await message.answer("⬅️ Включена предыдущая серия")
    else:
        await message.answer("❌ Не удалось найти окно с видео")

@dp.message(F.text == "➡️ Следующая серия")
async def next_episode(message: types.Message):
    if send_input_key(ord('N')):  # Клавиша N
        await message.answer("➡️ Включена следующая серия")
    else:
        await message.answer("❌ Не удалось найти окно с видео")

@dp.message(F.text == "🔍 Поиск аниме")
async def search_anime(message: types.Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_title)
    await message.answer("Введите название аниме для поиска:")

@dp.message(SearchStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    search_query = message.text
    db.log_command(message.from_user.id, f"search_anime:{search_query}")
    
    await message.answer(f"🔍 {hitalic('Ищу аниме')} {hbold(search_query)}...", parse_mode="HTML")
    
    try:
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        url = f"https://rutube.ru/api/search/video/?query={search_query}+аниме&format=json"
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if not data.get('results'):
            await message.answer("❌ Ничего не найдено.")
            return

        # Формируем клавиатуру с результатами
        keyboard = []
        for result in data['results'][:5]:
            title = result.get('title', '').strip()[:50]
            video_id = result.get('id', '')
            if title and video_id:
                # Используем более короткий callback_data
                keyboard.append([InlineKeyboardButton(
                    text=f"🎬 {title}",
                    callback_data=f"v:{video_id}"
                )])

        await message.answer(
            "Выберите аниме:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await message.answer("❌ Произошла ошибка при поиске.")
    finally:
        await state.clear()

@dp.callback_query(lambda c: c.data.startswith('v:'))
async def process_anime_selection(callback_query: types.CallbackQuery):
    try:
        video_id = callback_query.data.split(':')[1]
        url = f"https://rutube.ru/video/{video_id}/"
        
# Получаем информацию о видео для логирования
        api_url = f"https://rutube.ru/api/video/{video_id}/"
        response = requests.get(api_url)
        video_data = response.json()
        title = video_data.get('title', 'Неизвестное видео')

        db.log_anime_view(callback_query.from_user.id, title)
        await callback_query.message.answer(f"▶️ Запускаю: {title}")

        webbrowser.open(url)
        
        # Ждем загрузки страницы и плеера
        await asyncio.sleep(7)
        
        # Последовательность действий для включения полноэкранного режима
        if send_input_key(0x46):  # 'F'
            await callback_query.message.answer("✅ Видео запущено в полноэкранном режиме")
        else:
            # Пробуем альтернативный метод
            send_input_key(0x0D)  # Enter для фокуса на плеере
            await asyncio.sleep(0.5)
            send_input_key(0x46)  # F снова
            await callback_query.message.answer("✅ Видео запущено")
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске видео: {e}")
        await callback_query.message.answer("❌ Ошибка при запуске видео")

# Инициализация обработчика голоса
voice_handler = VoiceHandler()

@dp.message(F.voice)
async def handle_voice(message: types.Message, state: FSMContext):
    try:
        # Сообщаем о начале обработки
        processing_msg = await message.answer("🎧 Обрабатываю голосовое сообщение...")
        
        # Получаем файл голосового сообщения
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Создаем временную директорию
        os.makedirs("temp", exist_ok=True)
        voice_path = os.path.join("temp", f"voice_{message.message_id}.ogg")
        
        try:
            # Скачиваем файл
            await bot.download_file(file_path, voice_path)
            
            # Распознаем команду
            text = voice_handler.recognize_command(voice_path)
            
            if not text:
                await processing_msg.edit_text("❌ Не удалось распознать команду. Пожалуйста, повторите.")
                return
            
            # Логируем распознанный текст
            logger.info(f"Распознан текст: {text}")
            await processing_msg.edit_text(f"✅ Распознано: {text}")
            
            # Парсим команду
            command, query = voice_handler.parse_command(text)
            
            if not command:
                await message.answer("❓ Не поняла команду. Попробуйте еще раз.")
                return
            
            # Обрабатываем команду
            await process_voice_command(message, command, query, state)
            
        finally:
            # Удаляем временные файлы
            try:
                if os.path.exists(voice_path):
                    os.remove(voice_path)
            except Exception as e:
                logger.error(f"Ошибка при удалении временного файла: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка обработки голосового сообщения: {e}")
        await message.answer("❌ Произошла ошибка при обработке голосового сообщения")

async def process_voice_command(message: types.Message, command: str, query: str, state: FSMContext):
    """Отдельная функция для обработки распознанных голосовых команд"""
    try:
        if command == "search":
            results = voice_handler.search_anime(query)
            if results:
                search_results[message.from_user.id] = results
                await state.set_state(SearchStates.waiting_for_choice)
        elif command == "select":
            current_state = await state.get_state()
            if current_state == "SearchStates:waiting_for_choice":
                user_results = search_results.get(message.from_user.id, [])
                if 1 <= query <= len(user_results):
                    selected_video = user_results[query - 1]
                    video_id = selected_video.get('id', '')
                    if video_id:
                        await process_anime_selection_voice(message, video_id)
                        await state.clear()
                        search_results.pop(message.from_user.id, None)
                        return
                await message.answer("❌ Неверный номер. Пожалуйста, выберите существующий вариант.")
        else:
            # Медиа команды
            command_map = {
                "forward": (0x27, "⏩ Перемотка вперед"),
                "backward": (0x25, "⏪ Перемотка назад"),
                "next": (0x4E, "➡️ Следующая серия"),
                "previous": (0x50, "⬅️ Предыдущая серия")
            }
            
            if command in command_map:
                key_code, message_text = command_map[command]
                if send_input_key(key_code):
                    await message.answer(message_text)
                else:
                    await message.answer("❌ Не удалось выполнить команду")
            
    except Exception as e:
        logger.error(f"Ошибка обработки команды {command}: {e}")
        await message.answer("❌ Ошибка при выполнении команды")

async def process_anime_selection_voice(message: types.Message, video_id: str):
    try:
        url = f"https://rutube.ru/video/{video_id}/"
        
        # Получаем информацию о видео для логирования
        api_url = f"https://rutube.ru/api/video/{video_id}/"
        response = requests.get(api_url)
        video_data = response.json()
        title = video_data.get('title', 'Неизвестное видео')

        db.log_anime_view(message.from_user.id, title)
        voice_handler.speak(f"Запускаю видео: {title}")
        await message.answer(f"▶️ Запускаю: {title}")

        webbrowser.open(url)
        
        await asyncio.sleep(7)
        
        if send_input_key(0x46):  # 'F'
            await message.answer("✅ Видео запущено в полноэкранном режиме")
        else:
            send_input_key(0x0D)
            await asyncio.sleep(0.5)
            send_input_key(0x46)
            await message.answer("✅ Видео запущено")
        
    except Exception as e:
        logger.error(f"Ошибка при запуске видео: {e}")
        await message.answer("❌ Ошибка при запуске видео")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
