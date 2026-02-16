import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from main import run_analysis
from scanner import (
    scan_top10_fundamental_cheapest,
    scan_top10_technical_4of4,
    scan_top10_combo,
    scan_top10_undervalued_strong,
    scan_top10_breakout,
    format_fundamental_message,
    format_technical_message,
    format_combo_message,
    format_undervalued_message,
    format_breakout_message,
)


TOKEN = "8421191326:AAHmMfMWUDdwmERxKNyDDChDiqUGhdN7vYA"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TELEGRAM_MAX = 3800  # aman di bawah limit Telegram 4096


async def send_long(update: Update, text: str):
    """Kirim teks panjang dengan memecah jadi beberapa pesan."""
    if not text:
        await update.message.reply_text("(Tidak ada output)")
        return
    for i in range(0, len(text), TELEGRAM_MAX):
        await update.message.reply_text(text[i:i + TELEGRAM_MAX])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📊 *IDX Smart Scanner Bot*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "🔎 *Analisa 1 Saham*\n"
        "Ketik langsung kode saham:\n"
        "`BBCA`  `BBRI`  `ADRO`\n\n"

        "📈 *Fitur Scanner:*\n\n"

        "/fundamental\n"
        "💰Top 10 Valuasi Termurah (berdasarkan PE)\n\n"

        "/technical\n"
        "📊Top 10 Teknikal Score 4/4\n\n"

        "/combo\n"
        "🏆Ranking Gabungan Fundamental + Teknikal\n\n"

        "/undervalued\n"
        "💎Top 10 Undervalued + Strong Trend\n\n"

        "/breakout\n"
        "🚀Top 10 Breakout Candidate\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ Data harga & fundamental real-time\n"
        "📌 Gunakan dengan bijak untuk keputusan investasi\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )


async def fundamental(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Scanning Top 10 Fundamental termurah (PE), Butuh waktu selama 1-2 menit")
    loop = asyncio.get_running_loop()

    try:
        top, meta = await loop.run_in_executor(None, scan_top10_fundamental_cheapest)
        msg = format_fundamental_message(top, meta)
        await send_long(update, msg)

    except Exception as e:
        logging.exception("Error saat scan fundamental")
        await update.message.reply_text(f"❌ Error saat scan fundamental:\n{repr(e)}")


async def technical(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Scanning Top 10 Technical (Score 4/4), Butuh waktu selama 1-2 menit")
    loop = asyncio.get_running_loop()

    try:
        top, meta = await loop.run_in_executor(None, scan_top10_technical_4of4)
        msg = format_technical_message(top, meta)
        await send_long(update, msg)

    except Exception as e:
        logging.exception("Error saat scan technical")
        await update.message.reply_text(f"❌ Error saat scan technical:\n{repr(e)}")

async def combo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏆 Ranking Gabungan Fundamental + Teknikal... (1-2 menit)")
    loop = asyncio.get_running_loop()
    try:
        top, meta = await loop.run_in_executor(None, scan_top10_combo)
        msg = format_combo_message(top, meta)
        await send_long(update, msg)
    except Exception as e:
        logging.exception("Error saat scan combo")
        await update.message.reply_text(f"❌ Error saat scan combo:\n{repr(e)}")


async def undervalued(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 Top 10 Undervalued + Strong Trend... (1-2 menit)")
    loop = asyncio.get_running_loop()
    try:
        top, meta = await loop.run_in_executor(None, scan_top10_undervalued_strong)
        msg = format_undervalued_message(top, meta)
        await send_long(update, msg)
    except Exception as e:
        logging.exception("Error saat scan undervalued")
        await update.message.reply_text(f"❌ Error saat scan undervalued:\n{repr(e)}")


async def breakout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Top 10 Breakout Candidate... (1-2 menit)")
    loop = asyncio.get_running_loop()
    try:
        top, meta = await loop.run_in_executor(None, scan_top10_breakout)
        msg = format_breakout_message(top, meta)
        await send_long(update, msg)
    except Exception as e:
        logging.exception("Error saat scan breakout")
        await update.message.reply_text(f"❌ Error saat scan breakout:\n{repr(e)}")

        
async def analyze_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = update.message.text.strip().upper()
    await update.message.reply_text(f"🔎 Menganalisa {ticker} ...")

    try:
        hasil = run_analysis(ticker)
        await send_long(update, hasil)

        if os.path.exists("chart.png"):
            with open("chart.png", "rb") as f:
                await update.message.reply_photo(photo=f)

        await update.message.reply_text("✅ Analisa selesai.")

    except Exception as e:
        logging.exception("Error saat analisa saham")
        await update.message.reply_text(f"❌ Terjadi error:\n{repr(e)}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fundamental", fundamental))
    app.add_handler(CommandHandler("technical", technical))
    app.add_handler(CommandHandler("combo", combo))
    app.add_handler(CommandHandler("undervalued", undervalued))
    app.add_handler(CommandHandler("breakout", breakout))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_stock))

    print("Bot berjalan...")
    app.run_polling()