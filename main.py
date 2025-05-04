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
import pyautogui
import subprocess

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

# Обработчики кнопок управления аниме
@dp.message(F.text == "⏸ Пауза/Продолжить")
async def toggle_pause(message: types.Message):
    db.log_command(message.from_user.id, "pause_play")
    pyautogui.press('space')
    await message.answer("⏸ Пауза/Продолжить воспроизведение")

@dp.message(F.text == "⏩ Вперед 10 сек")
async def forward_10(message: types.Message):
    db.log_command(message.from_user.id, "forward")
    pyautogui.press('right')
    await message.answer("⏩ Перемотка вперед на 10 секунд")

@dp.message(F.text == "⏪ Назад 10 сек")
async def backward_10(message: types.Message):
    db.log_command(message.from_user.id, "backward")
    pyautogui.press('left')
    await message.answer("⏪ Перемотка назад на 10 секунд")

@dp.message(F.text == "⬅️ Предыдущая серия")
async def previous_episode(message: types.Message):
    db.log_command(message.from_user.id, "previous_episode")
    pyautogui.press('p')  # предполагаем, что 'p' - клавиша для предыдущей серии
    await message.answer("⬅️ Включена предыдущая серия")

@dp.message(F.text == "➡️ Следующая серия")
async def next_episode(message: types.Message):
    db.log_command(message.from_user.id, "next_episode")
    pyautogui.press('n')
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
    
    # Поиск на RUTUBE
    url = f"https://rutube.ru/search/?query={search_query}+аниме"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Найти все результаты поиска (примерная структура, может потребоваться адаптация)
    results = soup.find_all('div', class_='search-item')
    
    if not results:
        await message.answer("Ничего не найдено")
        await state.clear()
        return

    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for result in results[:5]:  # Ограничим до 5 результатов
        title = result.find('a').text
        link = "https://rutube.ru" + result.find('a')['href']
        keyboard.add(InlineKeyboardButton(
            text=f"🎬 {title}", 
            callback_data=f"anime:{link}:{title}"
        ))

    await message.answer("Найденные аниме:", reply_markup=keyboard)
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
    pyautogui.press('f')
    
    await callback_query.message.answer("Аниме запущено в полноэкранном режиме")
    await callback_query.answer()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
