import os
import datetime
import gspread
import logging
from dotenv import load_dotenv
from gspread_formatting import CellFormat, Color, format_cell_range, Border, borders

from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Авторизация в Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

import json
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if not json_str:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")

# Значение переменной — это JSON-строка; распарсим её в dict
service_info = json.loads(json_str)
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_info, scope)
client = gspread.authorize(creds)

# Названия столбцов
COLUMNS = [
    "Дата", "Водитель (ФИО)", "Транспорт", "Номер транспорта",
    "Наименование груза", "Количество топлива", "Вид топлива",
    "Маршрут", "Расстояние (км)", "Машина (час)", "Остаток топлива", "Примечание"
]

# Функция создания новой вкладки по месяцу
def get_or_create_month_worksheet():
    sheet = client.open_by_key(SPREADSHEET_ID)
    month_name = datetime.datetime.now().strftime('%B')
    try:
        worksheet = sheet.worksheet(month_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=month_name, rows="100", cols="20")
        worksheet.append_row(COLUMNS)
    return worksheet

# Форматирование рамок
def apply_borders(worksheet, cell_range):
    border_format = CellFormat(borders=borders(
        top=Border("SOLID"), bottom=Border("SOLID"),
        left=Border("SOLID"), right=Border("SOLID")
    ))
    format_cell_range(worksheet, cell_range, border_format)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь данные в формате:\n"
                                    "ФИО Транспорт Номер Груз Кол-во ВидТоплива Маршрут КМ МашЧас Остаток Примечание")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    parts = msg.split()
    
    if len(parts) < 11:
        await update.message.reply_text("Недостаточно данных. Убедитесь, что вы указали все поля.")
        return

    now = datetime.datetime.now()
    today = now.strftime("%d.%m.%Y")
    worksheet = get_or_create_month_worksheet()

    # Парсинг
    komu = parts[0]
    vid = parts[1]
    nomer = parts[2]
    naimenovanie = parts[3]
    kolvo = parts[4]
    vid_topliva = parts[5]
    marshrut = parts[6]
    km = parts[7]
    mash_chas = parts[8]
    ostatok = parts[9]
    primechanie = " ".join(parts[10:])

    # Добавление строки
    row = [today, komu, vid, nomer, naimenovanie, kolvo, vid_topliva, marshrut, km, mash_chas, ostatok, primechanie]
    worksheet.append_row(row)

    # Форматирование границ
    last_row = len(worksheet.get_all_values())
    cell_range = f"A{last_row}:L{last_row}"
    apply_borders(worksheet, cell_range)

    await update.message.reply_text("✅ Данные успешно добавлены!")

# Запуск бота
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()