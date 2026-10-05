import asyncio
import secrets
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = "8863858348:AAEl7aOuzEN-QFKv8ix8o85n39x_N2O_nPs"
BASE_URL = "https://example.com/survey"

# Hakikisha ID ya channel ni sahihi na bot ni ADMIN humo ndani
CHANNEL_ID = -1003848042879
INVITE_LINK = "https://t.me/+p2lvqqQ43Xw5ZGZk"

user_tokens = {}

# ==================== MEMBERSHIP VERIFICATION ====================

ALLOWED_STATUSES = [
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
    ChatMemberStatus.RESTRICTED,
    "member",
    "administrator",
    "creator",
    "restricted",
]

async def is_user_member(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Kama ni restricted, thibitisha kama bado ni mwanachama
        if getattr(member, "is_member", True):
            if member.status in ALLOWED_STATUSES:
                return True
        return False
    except Exception as e:
        # Hii itaandika kosa halisi kwenye Command Prompt (CMD)
        print(f"[ERROR UKAGUZI] User ID: {user_id} | Sababu: {e}")
        return False

def get_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Our Channel", url=INVITE_LINK)],
        [InlineKeyboardButton("⚡ Verify & Unlock Bot", callback_data="verify_join")]
    ])

def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Get Facebook Link", callback_data="btn_facebook")],
        [
            InlineKeyboardButton("🔄 Regenerate Link", callback_data="btn_newlink"),
            InlineKeyboardButton("🛑 Stop Link", callback_data="btn_stop")
        ],
        [InlineKeyboardButton("📢 Official Channel", url=INVITE_LINK)]
    ])

WELCOME_TEXT = (
    "✨ *Welcome to Your Dashboard* ✨\n\n"
    "Select an option below using the interactive buttons:\n\n"
    "• *Facebook Link:* Generates your unique personalized link.\n"
    "• *Regenerate Link:* Revokes the old link and creates a new one.\n"
    "• *Stop Link:* Deactivates your current active link.\n\n"
    "--------------------\n"
    "_Developed by: @Nexus873_"
)

# ==================== START COMMAND ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not await is_user_member(context.bot, user_id):
        await update.message.reply_text(
            "🔒 *Access Denied!*\n\n"
            "Please join our official channel first to unlock all features.\n\n"
            "Click the button below to join, then click *'Verify & Unlock Bot'*:",
            reply_markup=get_join_keyboard(),
            parse_mode="Markdown"
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(0.5)

    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown"
    )

# ==================== LINK GENERATION ====================

def generate_unique_link(chat_id: int) -> str:
    token = secrets.token_urlsafe(12)
    user_tokens[chat_id] = token
    return f"{BASE_URL}?token={token}"

async def process_and_send_link(chat_id: int, bot):
    status_msg = await bot.send_message(
        chat_id=chat_id,
        text="⏳ `Checking your subscription...`",
        parse_mode="Markdown"
    )
    await asyncio.sleep(0.6)

    await status_msg.edit_text("🔄 `Generating unique link...`", parse_mode="Markdown")
    await asyncio.sleep(0.7)

    await status_msg.edit_text("⚡ `Finalizing configuration...`", parse_mode="Markdown")
    await asyncio.sleep(0.5)

    link = generate_unique_link(chat_id)

    final_text = (
        "✅ *Process Completed!*\n\n"
        "🔵 *Your Facebook Link:*\n"
        f"`{link}`\n\n"
        "📌 *Important Notes:*\n"
        "• This link is unique and bound to your account.\n"
        "• Requesting a new link will deactivate this one.\n\n"
        "--------------------\n"
        "_Developed by: @Nexus873_"
    )

    action_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Regenerate Link", callback_data="btn_newlink")],
        [InlineKeyboardButton("🛑 Stop This Link", callback_data="btn_stop")]
    ])

    await status_msg.edit_text(final_text, reply_markup=action_buttons, parse_mode="Markdown")

# ==================== CALLBACK QUERY HANDLER ====================

async def handle_callback_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id

    # Kitufe cha Verify
    if data == "verify_join":
        if await is_user_member(context.bot, user_id):
            await query.message.edit_text(
                WELCOME_TEXT,
                reply_markup=get_main_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ Verification failed! Make sure you actually joined the channel.", show_alert=True)
        return

    # Ukaguzi wa uanachama kabla ya huduma yoyote
    if not await is_user_member(context.bot, user_id):
        await query.message.reply_text(
            "🔒 Please join our official channel first to continue:",
            reply_markup=get_join_keyboard(),
            parse_mode="Markdown"
        )
        return

    if data in ["btn_facebook", "btn_newlink"]:
        await process_and_send_link(chat_id, context.bot)

    elif data == "btn_stop":
        if chat_id in user_tokens:
            del user_tokens[chat_id]
            await query.message.reply_text("🛑 *Active link has been disabled.*", parse_mode="Markdown")
        else:
            await query.message.reply_text("ℹ️ No active link found.")

# ==================== COMMAND HANDLERS ====================

async def get_facebook_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_member(context.bot, user_id):
        await update.message.reply_text("🔒 Please join our channel first:", reply_markup=get_join_keyboard())
        return
    await process_and_send_link(update.effective_chat.id, context.bot)

async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📢 *Official Channel:*\n{INVITE_LINK}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Open Channel ↗️", url=INVITE_LINK)]]),
        parse_mode="Markdown"
    )

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_tokens:
        del user_tokens[chat_id]
        await update.message.reply_text("🛑 *Active link has been disabled.*", parse_mode="Markdown")
    else:
        await update.message.reply_text("ℹ️ No active link found.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("facebook", get_facebook_command))
    app.add_handler(CommandHandler("newlink", get_facebook_command))
    app.add_handler(CommandHandler("channel", channel_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CallbackQueryHandler(handle_callback_buttons))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()