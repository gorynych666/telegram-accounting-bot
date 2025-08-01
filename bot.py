import os
import json
from datetime import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Загрузка переменных из .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

# Подключение к Google Sheets
creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gc = gspread.authorize(credentials)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# Получение названия листа по текущему месяцу
def get_current_month_sheet():
    month_name = datetime.now().strftime('%B')
    try:
        return spreadsheet.worksheet(month_name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=month_name, rows="100", cols="10")

# Разбор сообщения и запись в таблицу
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()

    if not parts or len(parts) < 3:
        await update.message.reply_text("❌ Формат: Кому Вид Кол-во [Дата] [Примечание]")
        return

    кому = parts[0]
    вид = parts[1]
    кол_во = parts[2]

    дата = datetime.now().strftime("%d.%m.%Y")
    примечание = ""

    if len(parts) >= 4:
        if "." in parts[3]:
            дата = parts[3]
            if len(parts) > 4:
                примечание = " ".join(parts[4:])
        else:
            примечание = " ".join(parts[3:])

    sheet = get_current_month_sheet()
    row = [кому, вид, кол_во, дата, примечание]
    sheet.append_row(row)

    await update.message.reply_text("✅ Данные записаны!")

# Команда старта
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Введи данные в формате:\nКому Вид Кол-во [Дата] [Примечание]")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Автонастройка Webhook
    PORT = int(os.environ.get("PORT", 8443))
    URL = f"{RENDER_EXTERNAL_URL}/webhook"

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=URL
    )