import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext, CallbackQueryHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SELECT_ROOM, DESCRIBE_PROBLEM, CONTACT_NAME, CONTACT_PHONE, ANOTHER_REQUEST = range(5)

# Початок взаємодії з ботом
def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    reply_markup = get_navigation_keyboard()

    update.message.reply_text(
        f"Привіт, {user.first_name}!\n"
        "Це технічний бот ІТ факультету. За допомогою нього ви можете подати заявку про несправності в 15 корпусі НУБіП України.\n"
        "Оберіть опцію, щоб продовжити.",
        reply_markup=reply_markup
    )

    return ANOTHER_REQUEST

# Команда /help
def help_command(update: Update, context: CallbackContext):
    help_text = (
        "Це технічний бот ІТ факультету. Ви можете:\n\n"
        "/start - почати взаємодію з ботом\n"
        "/help - показати довідку\n"
        "/menu - показати початкове меню\n\n"
        "Подача заявки:\n"
        "1. Виберіть 'Створити заявку' або 'Зв'язатися з фахівцями'.\n"
        "2. Введіть номер аудиторії, опис проблеми, ваше ім'я та номер телефону.\n"
        "3. Заявка буде оброблена.\n\n"
        "Зв'язок з фахівцями:\n"
        "- Оберіть 'Зв'язатися з фахівцями'.\n"
        "- Виберіть фахівця для зв'язку через Telegram."
    )

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Створити заявку", callback_data='create_request')],
        [InlineKeyboardButton("Зв'язатися з фахівцями", callback_data='contact_specialists')]
    ])

    update.message.reply_text(help_text, reply_markup=reply_markup)

# Отримати клавіатуру навігації
def get_navigation_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Створити заявку", callback_data='create_request')],
        [InlineKeyboardButton("Зв'язатися з фахівцями", callback_data='contact_specialists')]
    ])

# Зберегти заявку до електронної таблиці
def save_request_to_spreadsheet(request_data):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('itsupportbot-396415-d94d5c2ad4d0.json', scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open("Заявки")
    worksheet = spreadsheet.get_worksheet(0)
    worksheet.append_row([request_data.get('name', ''), request_data.get('room', ''), request_data.get('problem', ''), request_data.get('phone', '')])

# Вибір номера аудиторії
def select_room(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    room = update.message.text

    context.user_data['room'] = room

    update.message.reply_text(f"Добре, {user.first_name}! Тепер опишіть, будь ласка, коротко проблему.")
    return DESCRIBE_PROBLEM

# Опис проблеми
def describe_problem(update: Update, context: CallbackContext) -> int:
    problem = update.message.text
    context.user_data['problem'] = problem
    update.message.reply_text("Дякуємо за опис проблеми. Введіть ваше ім'я.")
    return CONTACT_NAME

# Контактне ім'я
def contact_name(update: Update, context: CallbackContext) -> int:
    name = update.message.text
    context.user_data['name'] = name
    update.message.reply_text("Введіть ваш номер телефону.")
    return CONTACT_PHONE

# Контактний телефон
def contact_phone(update: Update, context: CallbackContext) -> int:
    phone = update.message.text
    context.user_data['phone'] = phone
    update.message.reply_text(
        "Дякуємо за введену інформацію! Ваша заявка буде оброблена найближчим часом.\n"
        "Якщо бажаєте, можете створити ще одну заявку або зв'язатися з фахівцями.",
        reply_markup=get_navigation_keyboard()
    )
    save_request_to_spreadsheet(context.user_data)
    return ANOTHER_REQUEST

# Інша заявка або зв'язок з фахівцями
def another_request(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query.data == 'create_request':
        query.message.reply_text("Введіть номер аудиторії.")
        return SELECT_ROOM
    elif query.data == 'contact_specialists':
        specialists_links = [
            "https://t.me/ZargO_0",
            "https://t.me/alexkole",
            "https://t.me/zekapaupau",
            "https://t.me/passipamper"
        ]
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Фахівець 1", url=specialists_links[0])],
            [InlineKeyboardButton("Фахівець 2", url=specialists_links[1])],
            [InlineKeyboardButton("Фахівець 3", url=specialists_links[2])],
            [InlineKeyboardButton("Фахівець 4", url=specialists_links[3])],
            [InlineKeyboardButton("Створити заявку", callback_data='create_request')]
        ])
        query.message.reply_text("Оберіть фахівця для зв'язку:", reply_markup=reply_markup)
        return ANOTHER_REQUEST

# Функція для відображення початкового меню
def show_start_menu(update: Update, context: CallbackContext):
    reply_markup = get_navigation_keyboard()
    update.message.reply_text(
        "Ось ваше початкове меню:",
        reply_markup=reply_markup
    )
    return ANOTHER_REQUEST

# Головна функція
def main() -> None:
    bot_token = "6525775467:AAGlS1IZxe06z-1CcjEI0DOafyLIRofN51o"

    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_ROOM: [MessageHandler(Filters.text & ~Filters.command, select_room)],
            DESCRIBE_PROBLEM: [MessageHandler(Filters.text & ~Filters.command, describe_problem)],
            CONTACT_NAME: [MessageHandler(Filters.text & ~Filters.command, contact_name)],
            CONTACT_PHONE: [MessageHandler(Filters.text & ~Filters.command, contact_phone)],
            ANOTHER_REQUEST: [
                CallbackQueryHandler(another_request, pattern='create_request'),
                CallbackQueryHandler(another_request, pattern='contact_specialists')
            ]
        },
        fallbacks=[
            CommandHandler('help', help_command),
            CommandHandler('menu', show_start_menu)  # Додайте обробник команди /menu тут
        ],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
