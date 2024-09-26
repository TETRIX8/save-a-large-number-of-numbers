import os
import re
import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Bot token
TOKEN = 'ваш токен'

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    waiting_for_name = State()  # State for entering name

# Keyboards
vcf_keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Создать VCF", callback_data="create_vcf"))
instruction_keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Получить инструкцию", callback_data="get_instruction"))

# Files for storing data
vip_users_file = 'vip_users.txt'
users_file = 'users.txt'
admin_id = 1404494933  # Admin ID

# Sticker list
STICKERS = [
    'CAACAgIAAxkBAAEH-D1myj2lxMS4WPRtiH0lujLtI-1YMwACVQADr8ZRGmTn_PAl6RC_NQQ',
    'CAACAgIAAxkBAAEH-FdmykDs-8EAAcLr1qZ9HGI5vPT4jDEAAkoDAAK1cdoGwn4G-ptIHsQ1BA'
]

# Variables for storing user names
user_names = {}  # Dictionary for storing user names

def load_vip_users():
    if os.path.exists(vip_users_file):
        with open(vip_users_file, 'r') as f:
            return set(map(int, f.read().split()))
    return set()

def save_vip_users(vip_users):
    with open(vip_users_file, 'w') as f:
        f.write('\n'.join(map(str, vip_users)))

vip_users = load_vip_users()

def load_users():
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return set(map(int, f.read().split()))
    return set()

def save_user(user_id):
    with open(users_file, 'a') as f:
        f.write(f"{user_id}\n")

all_users = load_users()

def random_sticker():
    return random.choice(STICKERS)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id

    if user_id not in all_users:
        all_users.add(user_id)
        save_user(user_id)
        await bot.send_message(admin_id, f"👤 Новый пользователь: {user_id}")
    
    welcome_text = (
        "👋 Привет! Я бот, который поможет вам обработать номера телефонов.\n\n"
        "📥 Отправьте мне .txt файл с номерами телефонов или просто текстовое сообщение с номерами.\n\n"
        "📝 После того как я обработаю номера, вы сможете получить отсортированный файл.\n"
        "📇 Также, вы можете создать VCF файл с контактами и сохранить его на своем устройстве.\n\n"
        "👇 Нажмите на кнопку ниже, чтобы получить дополнительную инструкцию или настройте имя контакта с помощью команды /rename."
    )
    await message.reply(welcome_text, reply_markup=instruction_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'get_instruction')
async def get_instruction(callback_query: types.CallbackQuery):
    instruction_text = (
        "📋 **Инструкция по использованию бота:**\n\n"
        "1️⃣ Отправьте мне .txt файл или текстовое сообщение с номерами телефонов.\n"
        "2️⃣ Я обработаю и отсортирую номера, и отправлю вам готовый файл.\n\n"
        "3️⃣ Вы можете создать VCF файл с контактами, нажав на кнопку 'Создать VCF'.\n\n"
        "4️⃣ Чтобы изменить имя контакта, используйте команду `/rename` и введите новое имя.\n\n"
        "Если у вас возникнут вопросы, просто напишите мне!"
    )
    await bot.send_message(callback_query.from_user.id, instruction_text, parse_mode='Markdown')
    await callback_query.answer()
@dp.message_handler(commands=['instry'])
async def instry_command(message: types.Message):
    instruction_text = (
        "📋 **Инструкция по использованию бота:**\n\n"
        "1️⃣ Отправьте мне .txt файл или текстовое сообщение с номерами телефонов.\n"
        "2️⃣ Я обработаю и отсортирую номера, и отправлю вам готовый файл.\n\n"
        "3️⃣ Вы можете создать VCF файл с контактами, нажав на кнопку 'Создать VCF'.\n\n"
        "4️⃣ Чтобы изменить имя контакта, используйте команду `/rename` и введите новое имя.\n\n"
        "Если у вас возникнут вопросы, просто напишите мне!"
    )
    await message.reply(instruction_text, parse_mode='Markdown')

@dp.message_handler(commands=['rename'])
async def rename_command(message: types.Message):
    user_id = message.from_user.id
    
    # Retrieve the current name, if set
    current_name = user_names.get(user_id, "Не установлено")

    # Prompt user for a new name
    await message.reply(
        f"✍️ Введите имя для контакта:\n\nТекущее имя: '{current_name}'"
    )
    
    # Set state to wait for the new name
    await Form.waiting_for_name.set()

@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id == admin_id:
        admin_text = (
            "🔧 **Админ панель**\n\n"
            "/add_vip [user_id] - Добавить пользователя в VIP список.\n"
            "/remove_vip [user_id] - Удалить пользователя из VIP списка.\n"
            "/list_vip - Показать список VIP пользователей.\n"
            "/broadcast [message] - Отправить сообщение всем пользователям."
        )

        # Send random sticker
        sticker_message = await bot.send_sticker(message.from_user.id, random_sticker())

        # Delay for 5 seconds and then delete sticker
        await asyncio.sleep(5)
        await bot.delete_message(message.from_user.id, sticker_message.message_id)

        await message.reply(admin_text)
    else:
        await message.reply("❌ У вас нет доступа к этой команде.")

@dp.message_handler(commands=['add_vip'])
async def add_vip(message: types.Message):
    if message.from_user.id != admin_id:
        await message.reply("❌ У вас нет доступа к этой команде.")
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.reply("❌ Неверный формат команды. Используйте /add_vip [user_id].")
        return

    user_id = int(parts[1])
    vip_users.add(user_id)
    save_vip_users(vip_users)
    await message.reply(f"✅ Пользователь {user_id} добавлен в VIP список.")

@dp.message_handler(commands=['remove_vip'])
async def remove_vip(message: types.Message):
    if message.from_user.id != admin_id:
        await message.reply("❌ У вас нет доступа к этой команде.")
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.reply("❌ Неверный формат команды. Используйте /remove_vip [user_id].")
        return

    user_id = int(parts[1])
    if user_id in vip_users:
        vip_users.remove(user_id)
        save_vip_users(vip_users)
        await message.reply(f"✅ Пользователь {user_id} удален из VIP списка.")
    else:
        await message.reply("❌ Пользователь не найден в VIP списке.")

@dp.message_handler(commands=['list_vip'])
async def list_vip(message: types.Message):
    if message.from_user.id != admin_id:
        await message.reply("❌ У вас нет доступа к этой команде.")
        return

    if not vip_users:
        await message.reply("📜 VIP список пуст.")
        return

    vip_list = "\n".join(str(user_id) for user_id in vip_users)
    await message.reply(f"📜 VIP пользователи:\n{vip_list}")

@dp.message_handler(commands=['broadcast'])
async def broadcast_message(message: types.Message):
    if message.from_user.id != admin_id:
        await message.reply("❌ У вас нет доступа к этой команде.")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("❌ Пожалуйста, введите сообщение для рассылки. Используйте /broadcast [message].")
        return

    broadcast_text = parts[1]

    # Send message to all users
    for user_id in all_users:
        try:
            await bot.send_message(user_id, broadcast_text)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    await message.reply("✅ Сообщение отправлено всем пользователям.")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    document = message.document

    if document.mime_type != 'text/plain':
        await message.reply("❌ Пожалуйста, отправьте текстовый файл (.txt).")
        return

    await document.download(destination_file='numbers.txt')

    with open('numbers.txt', 'r') as file:
        content = file.read()

    if not content.strip():
        await message.reply("❌ Файл пуст. Пожалуйста, отправьте файл с номерами.")
        os.remove('numbers.txt')
        return

    numbers = process_numbers(content)

    if not numbers:
        await message.reply("❌ Файл не содержит корректных номеров. Пожалуйста, отправьте файл с номерами в правильном формате.")
        os.remove('numbers.txt')
        return

    user_id = message.from_user.id

    # Send random sticker before processing
    sticker_message = await bot.send_sticker(user_id, random_sticker())

    # Delay for 5 seconds and then delete sticker
    await asyncio.sleep(5)
    await bot.delete_message(user_id, sticker_message.message_id)

    if user_id not in vip_users and len(numbers) > 100:
        numbers = numbers[:100]
        await message.reply(
            "❌ Вы можете обработать только до 100 номеров. Чтобы обработать больше, получите VIP-статус. "
            "Подробнее: @TETRIX_UNO"
        )

    sorted_file_name = 'sorted_numbers.txt'
    with open(sorted_file_name, 'w') as sorted_file:
        sorted_file.write('\n'.join(numbers))

    response_message = f"✅ Количество готовых номеров: {len(numbers)}"
    with open(sorted_file_name, 'rb') as sorted_file:
        await message.reply_document(sorted_file, caption=response_message, reply_markup=vcf_keyboard)

    os.remove('numbers.txt')

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    content = message.text

    numbers = process_numbers(content)

    if not numbers:
        await message.reply("❌ Сообщение не содержит корректных номеров. Пожалуйста, отправьте номера в правильном формате.")
        return

    user_id = message.from_user.id

    # Send random sticker before processing
    sticker_message = await bot.send_sticker(user_id, random_sticker())

    # Delay for 5 seconds and then delete sticker
    await asyncio.sleep(5)
    await bot.delete_message(user_id, sticker_message.message_id)

    if user_id not in vip_users and len(numbers) > 100:
        numbers = numbers[:100]
        await message.reply(
            "❌ Вы можете обработать только до 100 номеров. Чтобы обработать больше, получите VIP-статус. "
            "Подробнее: @TETRIX_UNO"
        )

    sorted_file_name = 'sorted_numbers.txt'
    with open(sorted_file_name, 'w') as sorted_file:
        sorted_file.write('\n'.join(numbers))

    response_message = f"✅ Количество готовых номеров: {len(numbers)}"
    with open(sorted_file_name, 'rb') as sorted_file:
        await message.reply_document(sorted_file, caption=response_message, reply_markup=vcf_keyboard)

@dp.callback_query_handler(lambda c: c.data == 'create_vcf')
async def create_vcf(callback_query: types.CallbackQuery):
    sorted_file_name = 'sorted_numbers.txt'
    vcf_filename = 'contacts.vcf'

    if not os.path.exists(sorted_file_name):
        await bot.send_message(callback_query.from_user.id, "❌ Файл с номерами не найден. Пожалуйста, загрузите файл с номерами или отправьте текст с номерами.")
        return

    user_id = callback_query.from_user.id
    name = user_names.get(user_id, 'Клиенты')  # Default to 'Клиенты' if name is not set

    with open(sorted_file_name, 'r') as f:
        lines = f.readlines()

    with open(vcf_filename, 'w') as vcf:
        for line in lines:
            client_number = line.strip()
            if re.match(r'^\+?\d+$', client_number):
                unique_id = str(hash(client_number))[-5:]
                vcf.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:{name} {client_number}\nTEL;TYPE=CELL:{client_number}\nUID:{unique_id}\nEND:VCARD\n")

    if os.path.getsize(vcf_filename) == 0:
        await bot.send_message(callback_query.from_user.id, "❌ Не удалось создать VCF файл. Проверьте формат номеров.")
        os.remove(vcf_filename)
        return

    # Send random sticker when creating VCF
    sticker_message = await bot.send_sticker(callback_query.from_user.id, random_sticker())

    # Delay for 5 seconds and then delete sticker
    await asyncio.sleep(5)
    await bot.delete_message(callback_query.from_user.id, sticker_message.message_id)

    with open(vcf_filename, 'rb') as vcf:
        await bot.send_document(
            callback_query.from_user.id,
            vcf,
            caption="✅ Контакты готовы для сохранения. Нажмите на файл для его скачивания."
        )

    os.remove(vcf_filename)
    await callback_query.answer()

@dp.message_handler(state=Form.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.text.strip()

    if not user_name:
        await message.reply("❌ Имя не может быть пустым. Пожалуйста, введите имя.")
        return

    user_names[user_id] = user_name
    

    # Send confirmation message with the current name
    await message.reply(f"Ваше текущее имя для контактов: '{user_name}' .\n"
     f"👌 Отправьте Номера для создание контактов "                   )

    await state.finish()

def process_numbers(content):
    """Function to process, clean, and sort numbers"""
    numbers = sorted(set(re.sub(r'\D', '', number) for number in content.split(",") if number.strip() and re.sub(r'\D', '', number)))
    numbers = [number for number in numbers if re.match(r'^\d+$', number)]
    return numbers

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

