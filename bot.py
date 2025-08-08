import os
import datetime
from dotenv import load_dotenv
import gspread
from gspread_formatting import format_cell_range, CellFormat, Border, Color, borders
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)
import nest_asyncio

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
SERVICE_ACCOUNT_FILE = "service_account.json"

# Подключение к Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
gc = gspread.authorize(credentials)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# Формат для границ ячеек
cell_border_format = CellFormat(
    borders=borders(
        top=Border("SOLID", Color(0, 0, 0)),
        bottom=Border("SOLID", Color(0, 0, 0)),
        left=Border("SOLID", Color(0, 0, 0)),
        right=Border("SOLID", Color(0, 0, 0)),
    )
)

# Создание листа, если не существует
def get_or_create_sheet(title):
    try:
        return spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows="1000", cols="20")

# Парсинг и обработка сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    values = message_text.split()

    if not values:
        await update.message.reply_text("Ошибка: пустое сообщение.")
        return

    # Названия столбцов
    headers = [
        "Дата", "Водитель (ФИО)", "Транспорт", "Номер транспорта", "Наименование груза",
        "Количество топлива", "Вид топлива", "Маршрут", "Расстояние (км)",
        "Машина (час)", "Остаток топлива", "Примечание"
    ]

    # Лист по текущему месяцу
    now = datetime.datetime.now()
    sheet_title = now.strftime("%B").capitalize()
    worksheet = get_or_create_sheet(sheet_title)

    # Проверка и установка заголовков
    if not worksheet.row_values(1):
        worksheet.insert_row(headers, index=1)

    # Автоматическое добавление даты, если не указано явно
    today = now.strftime("%d.%m.%Y")
    if len(values) == 11:
        values.insert(0, today)
    elif len(values) < 12:
        await update.message.reply_text("Ошибка: недостаточно данных.")
        return
    elif len(values) > 12:
        await update.message.reply_text("Ошибка: слишком много данных.")
        return

    worksheet.append_row(values)
    row_number = len(worksheet.get_all_values())
    cell_range = f"A{row_number}:L{row_number}"
    format_cell_range(worksheet, cell_range, cell_border_format)

    await update.message.reply_text("Данные успешно добавлены.")

# Запуск бота
if __name__ == "__main__":
    nest_asyncio.apply()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=RENDER_EXTERNAL_URL,
    )