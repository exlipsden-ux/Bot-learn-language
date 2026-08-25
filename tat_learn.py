import json
import os
import random
from typing import List, Dict, Tuple

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# === КОНФИГ ===
BOT_TOKEN = ""
ADMIN_ID = 

# Пути к файлам
DICT_PATH = "dictionary.json"
USER_DATA_PATH = "user_data.json"

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
tatar_to_russian: Dict[str, List[str]] = {}
russian_to_tatar: Dict[str, List[str]] = {}

# Загрузка и построение обратного словаря
def load_dictionaries():
    global tatar_to_russian, russian_to_tatar
    if not os.path.exists(DICT_PATH):
        raise FileNotFoundError(f"Файл {DICT_PATH} не найден!")
    with open(DICT_PATH, "r", encoding="utf-8") as f:
        tatar_to_russian = json.load(f)

    # Построим обратный словарь: русский -> татарский
    russian_to_tatar = {}
    for t_word, r_list in tatar_to_russian.items():
        for r_word in r_list:
            if r_word not in russian_to_tatar:
                russian_to_tatar[r_word] = []
            if t_word not in russian_to_tatar[r_word]:
                russian_to_tatar[r_word].append(t_word)

    print(f"Загружено: {len(tatar_to_russian)} татарских слов, {len(russian_to_tatar)} русских фраз.")

# Сохранение/загрузка данных пользователей
def load_user_data() -> dict:
    if os.path.exists(USER_DATA_PATH):
        with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_data(data: dict):
    with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === СОСТОЯНИЯ ===
class BotStates(StatesGroup):
    choosing_direction = State()
    answering = State()
    waiting_for_action = State()

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def get_user_data(user_id: str, user_ dict) -> dict:
    if user_id not in user_
        user_data[user_id] = {
            "direction": None,  # "tt->ru", "ru->tt", "both"
            "learned": [],      # выученные слова (словарные пары)
            "pool": [],         # текущие 10 слов для повторения
            "available_words": list(tatar_to_russian.keys())  # все слова, ещё не выученные
        }
    return user_data[user_id]

def get_random_word_pair(user_id: str, user_ dict) -> Tuple[str, str, str]:
    user = get_user_data(user_id, user_data)
    pool = user["pool"]
    direction = user["direction"]

    if not pool:
        return None, None, None

    word_pair = random.choice(pool)
    t_word, r_words = word_pair
    r_word = random.choice(r_words)

    if direction == "tt->ru":
        return t_word, r_word, "tt->ru"
    elif direction == "ru->tt":
        return r_word, t_word, "ru->tt"
    elif direction == "both":
        if random.choice([True, False]):
            return t_word, r_word, "tt->ru"
        else:
            return r_word, t_word, "ru->tt"
    return None, None, None

def update_pool(user_id: str, user_ dict):
    user = get_user_data(user_id, user_data)
    learned_set = set(tuple(pair) for pair in user["learned"])

    # Удалим выученные из пула
    user["pool"] = [pair for pair in user["pool"] if tuple(pair) not in learned_set]

    # Если в пуле < 10 — добавим новые слова (до 10)
    needed = 10 - len(user["pool"])
    available = [w for w in user["available_words"] if [w, tatar_to_russian[w]] not in user["pool"] and (w, tatar_to_russian[w]) not in learned_set]

    random.shuffle(available)
    to_add = available[:needed]

    for word in to_add:
        user["pool"].append([word, tatar_to_russian[word]])
        # удалим из доступных
        if word in user["available_words"]:
            user["available_words"].remove(word)

# === КНОПКИ ===
def get_main_menu():
    buttons = [
        [KeyboardButton(text="🔄 Начать обучение")],
        [KeyboardButton(text="📊 Моя статистика")],
        [KeyboardButton(text="📚 Повторить выученные")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_direction_kb():
    buttons = [
        [InlineKeyboardButton(text="С русского на татарский", callback_data="dir_ru->tt")],
        [InlineKeyboardButton(text="С татарского на русский", callback_data="dir_tt->ru")],
        [InlineKeyboardButton(text="Оба направления", callback_data="dir_both")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_feedback_kb():
    buttons = [
        [
            InlineKeyboardButton(text="👎 Не знаю", callback_data="feedback_0"),
            InlineKeyboardButton(text="🤔 Почти знаю", callback_data="feedback_1"),
            InlineKeyboardButton(text="👍 Выучил!", callback_data="feedback_2")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# === РОУТЕР ===
router = Router()

# === ХЕНДЛЕРЫ ===
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user_data_ref: dict):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id, user_data_ref)

    welcome1 = "Сәлам!\nБот татар сүзләренә өйрәтү өчен булдырылган. Ул яңа кешеләр өчен генә түгел, татар телен белүчеләр өчен дә булдырылган.\nБиредә сез үз белемнәрегезне тикшерә яки яңа, аз кулланыла торган сүзләрне өйрәнә аласыз."

    welcome2 = (
        "Сәлам! Я твой дружелюбный бот для изучения татарских слов и пополнения татарского словарного запаса. 😊\n"
        "В моей базе данных загружен перевод примерно 50 000 татарских слов.\n"
        "Я помогу тебе запомнить слова весело и эффективно: буду предлагать слово, ты пишешь перевод, я показываю правильный.\n\n"
        "Затем я предлагаю тебе оценить себя самому. На выбор будет 3 кнопки:\n"
        "👎 **Не знаю** — слово попадётся снова\n"
        "🤔 **Почти знаю** — слово повторится позже\n"
        "👍 **Выучил!** — слово больше не будет показываться (но можно повторить в меню)\n\n"
        "Слова повторяются, пока не отметишь 👍 — тогда добавлю новое. Начнём с 10 слов, чтобы было легко и мотивирующе!"
    )

    await message.answer(welcome1)
    await message.answer(welcome2, reply_markup=get_main_menu())
    await state.clear()

@router.message(F.text == "🔄 Начать обучение")
async def start_learning(message: Message, state: FSMContext, user_data_ref: dict):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id, user_data_ref)

    if user_data["direction"] is None:
        await message.answer("Выбери, как переводить слова:", reply_markup=get_direction_kb())
        await state.set_state(BotStates.choosing_direction)
    else:
        # Обновим пул и начнём
        update_pool(user_id, user_data_ref)
        word, correct, direction = get_random_word_pair(user_id, user_data_ref)
        if word is None:
            await message.answer("Пока нет слов для изучения. Попробуй позже!")
            return
        user_data["current_word"] = word
        user_data["current_correct"] = correct
        user_data["current_direction"] = direction

        if direction == "tt->ru":
            prompt = f"Переведи на русский:\n\n<b>{word}</b>"
        else:
            prompt = f"Переведи на татарский:\n\n<b>{word}</b>"

        await message.answer(prompt, parse_mode="HTML")
        await state.set_state(BotStates.answering)

@router.callback_query(StateFilter(BotStates.choosing_direction), F.data.startswith("dir_"))
async def direction_chosen(callback: CallbackQuery, state: FSMContext, user_data_ref: dict):
    user_id = str(callback.from_user.id)
    user_data = get_user_data(user_id, user_data_ref)

    mapping = {
        "dir_tt->ru": "tt->ru",
        "dir_ru->tt": "ru->tt",
        "dir_both": "both"
    }
    direction = mapping[callback.data]
    user_data["direction"] = direction

    await callback.message.edit_text("Направление выбрано! 🎯")
    await start_learning(callback.message, state, user_data_ref)
    await callback.answer()

@router.message(StateFilter(BotStates.answering))
async def handle_answer(message: Message, state: FSMContext, user_data_ref: dict):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id, user_data_ref)

    correct = user_data.get("current_correct", "???")
    direction = user_data.get("current_direction", "tt->ru")

    # Покажем правильный ответ
    if direction == "tt->ru":
        await message.answer(f"Правильный перевод: <b>{correct}</b>", parse_mode="HTML")
    else:
        await message.answer(f"Правильный перевод: <b>{correct}</b>", parse_mode="HTML")

    # Сохраним текущую пару для фидбека
    t_word = user_data["current_word"] if direction == "tt->ru" else correct
    r_words = user_data["current_correct"] if direction == "tt->ru" else [user_data["current_word"]]
    user_data["feedback_pair"] = [t_word, r_words if isinstance(r_words, list) else [r_words]]

    await message.answer("Как ты оцениваешь свой ответ?", reply_markup=get_feedback_kb())
    await state.set_state(BotStates.waiting_for_action)

@router.callback_query(StateFilter(BotStates.waiting_for_action), F.data.startswith("feedback_"))
async def handle_feedback(callback: CallbackQuery, state: FSMContext, user_data_ref: dict):
    user_id = str(callback.from_user.id)
    user_data = get_user_data(user_id, user_data_ref)
    feedback = int(callback.data.split("_")[1])

    pair = user_data["feedback_pair"]
    t_word, r_words = pair[0], pair[1]

    if feedback == 2:  # 👍 Выучил
        if pair not in user_data["learned"]:
            user_data["learned"].append(pair)
    # feedback == 0 или 1 — оставляем в пуле (ничего не делаем)

    # Обновим пул
    update_pool(user_id, user_data_ref)

    await callback.message.edit_text("Отлично! Продолжаем? 🚀")
    await start_learning(callback.message, state, user_data_ref)
    await callback.answer()

@router.message(F.text == "📊 Моя статистика")
async def show_stats(message: Message, user_data_ref: dict):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id, user_data_ref)
    learned = len(user_data["learned"])
    in_pool = len(user_data["pool"])
    total = learned + in_pool
    await message.answer(
        f"📈 Твоя статистика:\n"
        f"✅ Выучено: {learned}\n"
        f"🔄 В процессе: {in_pool}\n"
        f"📚 Всего слов: {total}\n\n"
        f"Продолжай в том же духе! 💪"
    )

@router.message(F.text == "📚 Повторить выученные")
async def repeat_learned(message: Message, user_data_ref: dict):
    user_id = str(message.from_user.id)
    user_data = get_user_data(user_id, user_data_ref)
    if not user_data["learned"]:
        await message.answer("У тебя пока нет выученных слов.")
        return

    pair = random.choice(user_data["learned"])
    t_word, r_words = pair[0], pair[1]
    r_word = random.choice(r_words)

    direction = random.choice(["tt->ru", "ru->tt"])
    if direction == "tt->ru":
        prompt = f"Повторим! Переведи на русский:\n\n<b>{t_word}</b>"
        correct = r_word
    else:
        prompt = f"Повторим! Переведи на татарский:\n\n<b>{r_word}</b>"
        correct = t_word

    await message.answer(prompt, parse_mode="HTML")
    await message.answer(f"Правильный ответ: <b>{correct}</b>", parse_mode="HTML")

# === АДМИН КОМАНДЫ ===
@router.message(Command("stats"))
async def admin_stats(message: Message, user_data_ref: dict):
    if message.from_user.id != ADMIN_ID:
        return
    total_users = len(user_data_ref)
    await message.answer(f"👥 Всего пользователей: {total_users}")

@router.message(Command("broadcast"))
async def admin_broadcast(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text[len("/broadcast "):]
    if not text:
        await message.answer("Используй: /broadcast <сообщение>")
        return
    user_data = load_user_data()
    success = 0
    for user_id in user_data.keys():
        try:
            await bot.send_message(int(user_id), text)
            success += 1
        except:
            pass
    await message.answer(f"Сообщение отправлено {success} пользователям.")

# === ЗАПУСК ===
async def main():
    load_dictionaries()
    user_data_ref = load_user_data()

    # Передаём user_data_ref в middleware или через контекст
    # В aiogram 3.x можно использовать startup/shutdown или замыкание
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp["user_data_ref"] = user_data_ref

    @dp.update.outer_middleware()
    async def inject_user_data(handler, event, data):
        data["user_data_ref"] = dp["user_data_ref"]
        return await handler(event, data)

    dp.include_router(router)

    # Сохраняем данные при завершении
    import asyncio
    try:
        await dp.start_polling(bot)
    finally:
        save_user_data(dp["user_data_ref"])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())