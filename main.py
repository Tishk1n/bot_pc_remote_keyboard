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
from ctypes import Structure, c_ulong, c_ushort, c_short, POINTER, windll, Union, c_void_p, sizeof, c_long, byref
import time

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

def send_key_press(key_code):
    """Отправка нажатия клавиши через SendInput"""
    try:
        extra = c_ulong(0)
        ii_ = INPUT_UNION()
        ii_.ki = KEYBDINPUT(key_code, 0, 0, 0, byref(extra))
        x = INPUT(c_ulong(1), ii_)
        windll.user32.SendInput(1, byref(x), sizeof(x))
        
        time.sleep(0.1)  # Небольшая задержка между нажатием и отпусканием
        
        ii_.ki = KEYBDINPUT(key_code, 0, 0x0002, 0, byref(extra))  # KEYEVENTF_KEYUP
        x = INPUT(c_ulong(1), ii_)
        windll.user32.SendInput(1, byref(x), sizeof(x))
        
    except Exception as e:
        logger.error(f"Ошибка при отправке клавиши через SendInput: {e}")

# Обновляем обработчики кнопок
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dp.message(F.text == "⏸ Пауза/Продолжить")
async def toggle_pause(message: types.Message):
    db.log_command(message.from_user.id, "pause_play")
    send_key_press(0x20)  # VK_SPACE
    await message.answer("⏸ Переключение паузы")

@dp.message(F.text == "⏩ Вперед 10 сек")
async def forward_10(message: types.Message):
    db.log_command(message.from_user.id, "forward")
    send_key_press(0x27)  # VK_RIGHT
    await message.answer("⏩ Перемотка вперед на 10 секунд")

@dp.message(F.text == "⏪ Назад 10 сек")
async def backward_10(message: types.Message):
    db.log_command(message.from_user.id, "backward")
    send_key_press(0x25)  # VK_LEFT
    await message.answer("⏪ Перемотка назад на 10 секунд")

@dp.message(F.text == "⬅️ Предыдущая серия")
async def previous_episode(message: types.Message):
    db.log_command(message.from_user.id, "previous_episode")
    send_key('P')
    await message.answer("⬅️ Включена предыдущая серия")

@dp.message(F.text == "➡️ Следующая серия")
async def next_episode(message: types.Message):
    db.log_command(message.from_user.id, "next_episode")
    send_key('N')
    await message.answer("➡️ Включена следующая серия")

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
        # Настройка запроса
        ua = UserAgent()
        headers = {
            'User-Agent': ua.random,
            'Accept': 'text/html',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Referer': 'https://rutube.ru/',
            'DNT': '1',
        }
        
        url = f"https://rutube.ru/api/search/video/?query={search_query}+аниме"
        response = requests.get(url, headers=headers)
        logger.debug(f"API ответ: {response.text[:200]}...")  # логируем часть ответа
        
        data = response.json()
        results = data.get('results', [])
        
        if not results:
            await message.answer("❌ Ничего не найдено. Попробуйте другой запрос.")
            await state.clear()
            return

        buttons = []
        row = []
        for result in results[:5]:
            title = result.get('title', '').strip()
            link = f"https://rutube.ru/video/{result.get('id', '')}/"
            
            if title and link:
                row.append(
                    InlineKeyboardButton(
                        text=f"🎬 {title[:50]}...", 
                        callback_data=f"anime:{link}:{title[:50]}"
                    )
                )
                if len(row) == 1:  # По одной кнопке в строке
                    buttons.append(row)
                    row = []
        
        if row:  # Добавляем оставшиеся кнопки
            buttons.append(row)
            
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("🎯 Найденные аниме:", reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await message.answer("❌ Произошла ошибка при поиске. Попробуйте позже.")
    
    finally:
        await state.clear()

@dp.callback_query(lambda c: c.data.startswith('anime:'))
async def process_anime_selection(callback_query: types.CallbackQuery):
    data = callback_query.data.split(':')
    link = data[1]
    title = data[2]
    
    db.log_anime_view(callback_query.from_user.id, title)
    await callback_query.message.answer(
        f"▶️ {hbold('Запускаю аниме:')} {hitalic(title)}",
        parse_mode="HTML"
    )
    
    # Открываем видео в браузере
    webbrowser.open(link)
    
    # Через небольшую задержку включаем полноэкранный режим
    await asyncio.sleep(3)
    send_key_press(0x70)  # VK_F1 = 0x70, соответствует клавише F
    
    await callback_query.message.answer("Аниме запущено в полноэкранном режиме")
    await callback_query.answer()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
