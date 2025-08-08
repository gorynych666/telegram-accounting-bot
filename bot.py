import os
import json
import base64
import datetime
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from gspread_formatting.dataframe import set_border

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
encoded_credentials = os.environ.get("GOOGLE_SERVICE_ACCOUNT_B64")

if not TELEGRAM_TOKEN or not SPREADSHEET_ID or not RENDER_EXTERNAL_URL or not encoded_credentials:
    raise ValueError("Не все переменные окружения заданы")

# Декодируем ключ из base64 и парсим JSON
try:
    decoded_json = base64.b64decode(encoded_credentials).decode("utf-8")
    creds_dict = json.loads(decoded_json)
except Exception as e:
    raise ValueError(f"Ошибка при декодировании GOOGLE_SERVICE_ACCOUNT_B64: {e}")

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

# Получить лист текущего месяца (на русском)
def get_current_month_sheet():
    month_name = datetime.datetime.now().strftime("%B")
    month_mapping = {
        "January": "Январь", "February": "Февраль", "March": "Март",
        "April": "Апрель", "May": "Май", "June": "Июнь",
        "July": "Июль", "August": "Август", "September": "Сентябрь",
        "October": "Октябрь", "November": "Ноябрь", "December": "Декабрь"
    }
    rus_month = month_mapping.get(month_name)

    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        return spreadsheet.worksheet(rus_month)
    except gspread.WorksheetNotFound:
        # Создаем лист, если его нет
        sheet = spreadsheet.add_worksheet(title=rus_month, rows="1000", cols="12")
        headers = [
            "Дата", "Водитель (ФИО)", "Транспорт", "Номер транспорта",
            "Наименование груза", "Количество топлива", "Вид топлива",
            "Маршрут", "Расстояние (км)", "Машина (час)", "Остаток топлива", "Примечание"
        ]
        sheet.append_row(headers)
        return sheet

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message_text = update.message.text.strip()
        parts = message_text.split(" ")

        # Простейший разбор — впоследствии можно доработать
        date = datetime.datetime.now().strftime("%d.%m.%Y")
        fio = parts[0] if len(parts) > 0 else ""
        transport = parts[1] if len(parts) > 1 else ""
        number = parts[2] if len(parts) > 2 else ""
        cargo = parts[3] if len(parts) > 3 else ""
        fuel_amount = parts[4] if len(parts) > 4 else ""
        fuel_type = parts[5] if len(parts) > 5 else ""
        route = parts[6] if len(parts) > 6 else ""
        distance = parts[7] if len(parts) > 7 else ""
        hours = parts[8] if len(parts) > 8 else ""
        fuel_left = parts[9] if len(parts) > 9 else ""
        note = " ".join(parts[10:]) if len(parts) > 10 else ""

        # Добавление строки
        sheet = get_current_month_sheet()
        row = [date, fio, transport, number, cargo, fuel_amount, fuel_type,
               route, distance, hours, fuel_left, note]
        sheet.append_row(row)

        # Добавление границ
        row_number = len(sheet.get_all_values())
        range_name = f"A{row_number}:L{row_number}"  # Столбцы A–L (12 столбцов)
        set_border(sheet, range_name,
                   top=True, bottom=True, left=True, right=True,
                   inner_horizontal=True, inner_vertical=True)

        await update.message.reply_text("✅ Данные добавлены в таблицу.")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        await update.message.reply_text(f"⚠️ Ошибка: {e}")

# Запуск приложения через Webhook (Render)
if __name__ == "__main__":
    from telegram.ext import Application

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    webhook_url = f"{RENDER_EXTERNAL_URL}"
    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=webhook_url,
    )