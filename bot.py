import os
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# 1. ከ @BotFather ያገኘኸው HTTP API Token
TOKEN = "9178391042:AAFZwPEi-qk1xElTV2DH-TqflXar7lHfYgI"

# 2. የአንተ የቴሌግራም Admin ID
ADMIN_ID = 462185736  

# 3. የእያንዳንዱ መጽሐፍ ስም፣ ዋጋ እና ትክክለኛ የ Google Drive ሊንክ
BOOKS = {
    "halwo": {
        "title": "መጽሐፈ ሀልዎ (399 ETB)",
        "link": "https://drive.google.com/file/d/1EAeHV7JMJ-zDY2ldgIjI6dSmsbWjwsAH/view?usp=drivesdk"
    },
    "alchemy": {
        "title": "የነፍስ አልኬሚ (250 ETB)",
        "link": "https://drive.google.com/file/d/1urCo2Y74KIoZnqlCK4xKYnNw4-aI6-Ap/view?usp=drivesdk"
    },
    "niqat": {
        "title": "መጽሐፈ ንቃት (200 ETB)",
        "link": "https://drive.google.com/file/d/1gVY33bjx97VMg80hZ3w5Ceee2M8DCpZz/view?usp=drivesdk"
    },
    "hailat": {
        "title": "የሰማይ ኃይላት (200 ETB)",
        "link": "https://drive.google.com/file/d/1fw8Qrwl7RWMZg91ceuBG1Aw-j08dPoS2/view?usp=drivesdk"
    },
    "el": {
        "title": "ኤል እና ማግ (50 ETB)",
        "link": "https://drive.google.com/file/d/1AKjmHy4SIc5RFFQ9RFwcogD2QVoFmZKF/view?usp=drivesdk"
    }
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Render Web Service እንዳያቋርጠው የሚያገለግል ሰርቨር
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running alive!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# ገዢው /start ሲል የመጽሐፍት ምርጫ ማሳየት
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📚 መጽሐፈ ሀልዎ - 399 ETB", callback_data="select_halwo")],
        [InlineKeyboardButton("📚 የነፍስ አልኬሚ - 250 ETB", callback_data="select_alchemy")],
        [InlineKeyboardButton("📚 መጽሐፈ ንቃት - 200 ETB", callback_data="select_niqat")],
        [InlineKeyboardButton("📚 የሰማይ ኃይላት - 200 ETB", callback_data="select_hailat")],
        [InlineKeyboardButton("📚 ኤል እና ማግ - 50 ETB", callback_data="select_el")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "ሰላም! እንኳን ወደ **መኖር** ዲጂታል መጽሐፍት መደብር በሰላም መጡ።\n\n"
        "እባክዎ መግዛት የሚፈልጉትን መጽሐፍ ከታች ይምረጡ፦",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ገዢው መጽሐፍ ሲመርጥ የክፍያ መረጃ መስጠት
async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("select_"):
        book_key = data.split("_")[1]
        context.user_data['selected_book'] = book_key
        book_title = BOOKS[book_key]["title"]
        
        await query.edit_message_text(
            f"✅ የመረጡት መጽሐፍ፡ **{book_title}**\n\n"
            "ክፍያውን ከታች ባሉት አካውንቶች ይፈጽሙ፦\n"
            "🏦 **ንግድ ባንክ (CBE):** `1000591686295`\n"
            "📱 **ቴሌብር (Telebirr):** `0920717750`\n"
            "👤 **ስም:** ቴዎድሮስ ግርማዬ\n\n"
            "📸 ክፍያውን እንደፈጸሙ **የደረሰኙን ፎቶ (Screenshot)** እዚህ ይላኩ።",
            parse_mode="Markdown"
        )

# ገዢው የደረሰኝ ፎቶ ሲልክ ለአድሚን ማሳወቅ
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    book_key = context.user_data.get('selected_book', 'halwo')
    book_title = BOOKS[book_key]["title"]
    
    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
        
        keyboard = [[InlineKeyboardButton("✅ አረጋግጥና ሊንክ ላክ (Approve)", callback_data=f"approve_{user.id}_{book_key}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=f"🔔 **አዲስ የክፍያ ደረሰኝ መጥቷል!**\n\n"
                    f"📚 **መጽሐፍ:** {book_title}\n"
                    f"👤 **ገዢ:** {user.first_name}\n"
                    f"🆔 **ID:** `{user.id}`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        await update.message.reply_text("⏳ ደረሰኝዎ በትክክል ደርሷል! እባክዎ ትንሽ ይጠብቁ፤ ሲረጋገጥ የመጽሐፉ ማውረጃ ሊንክ ወዲያውኑ ይላክልዎታል።")

# አንተ Approve ስትጫን የ Google Drive ሊንኩን ለገዢው መላክ
async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("approve_"):
        parts = data.split("_")
        user_id = int(parts[1])
        book_key = parts[2]
        
        book_title = BOOKS[book_key]["title"]
        drive_link = BOOKS[book_key]["link"]
        
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n✅ **ተረጋግጧል! የ Google Drive ሊንኩ ለገዢው ተልኳል።**",
            parse_mode="Markdown"
        )
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"🎉 **እንኳን ደስ አለዎት! ክፍያዎ ተረጋግጧል።**\n\n"
                     f"📚 **መጽሐፍ:** {book_title}\n"
                     f"📥 **መጽሐፉን ለማውረድ ከታች ያለውን ሊንክ ይጫኑ፦**\n\n"
                     f"👉 {drive_link}\n\n"
                     f"ስለገዙን እናመሰግናለን! መልካም ንባብ።",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.message.reply_text(f"❌ ሊንኩን መላክ አልተቻለም: {e}")

if __name__ == '__main__':
    # Dummy server ለ Render በጎን ማስኬድ
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_selection, pattern="^select_"))
    application.add_handler(CallbackQueryHandler(handle_approval, pattern="^approve_"))
    application.add_handler(MessageHandler(filters.PHOTO, handle_receipt))

    print("ቦቱ 24/7 በሰላም እየሰራ ነው...")
    application.run_polling()