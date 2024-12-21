import logging
from typing import Dict, Any
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# config
import yaml
def get_myconfig(_myconfig_file):
    with open(_myconfig_file, 'r', encoding="utf-8") as stream:
        #_myconfig = yaml.load(stream, Loader=yaml.CLoader)
        _myconfig = yaml.safe_load(stream)  # Replace yaml.load(stream, Loader=yaml.CLoader)
    return _myconfig
myconfig = get_myconfig("config.yml")
TOKEN = myconfig['Telegram']['token']
TARGET_CHAT_ID = myconfig['Telegram']['chat_id']
# Configuration
user_states: Dict[int, Dict[str, Any]] = {}

async def check_chat_id(update: Update) -> bool:
    """Verify if the update is from the target chat."""
    if not update.effective_chat:
        logger.warning("No chat information in update")
        return False
        
    current_chat_id = update.effective_chat.id
    if current_chat_id != TARGET_CHAT_ID:
        logger.warning(f"Received message from unauthorized chat: {current_chat_id}")
        if update.message:
            await update.message.reply_text("This bot is configured to work with a specific channel only.")
        return False
    return True

async def start(update: Update, context: CallbackContext) -> None:
    """Handle the /start command."""
    if not await check_chat_id(update):
        return

    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data='status'),
         InlineKeyboardButton("⚙️ Settings", callback_data='settings')],
        [InlineKeyboardButton("📈 Analytics", callback_data='analytics'),
         InlineKeyboardButton("❓ Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=TARGET_CHAT_ID,
        text="Channel Control Bot activated.\n"
             "What would you like to do?",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: CallbackContext) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    chat_id = query.message.chat.id
    
    # Check if callback is from target chat
    if chat_id != TARGET_CHAT_ID:
        await query.answer("Unauthorized chat", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == 'status':
        status_text = "🖥️ Channel Status:\n" + \
                     "Members: 1,234\n" + \
                     "Messages today: 56\n" + \
                     "Active threads: 3"
        await query.edit_message_text(text=status_text, reply_markup=get_back_keyboard())
        
    elif query.data == 'settings':
        keyboard = [
            [InlineKeyboardButton("🔔 Notifications", callback_data='notifications'),
             InlineKeyboardButton("⏰ Schedule", callback_data='schedule')],
            [InlineKeyboardButton("◀️ Back", callback_data='main_menu')]
        ]
        await query.edit_message_text(
            "⚙️ Channel Settings:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif query.data == 'main_menu':
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "Main Menu - Select an option:",
            reply_markup=keyboard
        )

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages and channel posts."""
    # Get the effective message (either direct message or channel post)
    effective_message = update.message or update.channel_post
    
    if not effective_message:
        logger.warning("Received update without message or channel post")
        return
        
    if not await check_chat_id(update):
        return
        
    try:
        # For any message (text or non-text), just show the main menu
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text="Welcome to the bot menu! Please select an option:",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Only try to reply if we have a valid message
        if effective_message:
            await context.bot.send_message(
                chat_id=TARGET_CHAT_ID,
                text="Error processing your message."
            )
        
    if not await check_chat_id(update):
        return
        
    try:
        message_text = update.message.text if update.message.text else "non-text message"
        
        # Process messages from the target channel
        await update.message.reply_text(
            f"Received message in target channel: {message_text}\n"
            "Please use the menu buttons for interaction.",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Only try to reply if we have a valid message
        if update.message:
            await update.message.reply_text("Error processing your message.")

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Create a keyboard with just a back button."""
    keyboard = [[InlineKeyboardButton("◀️ Back", callback_data='main_menu')]]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create the main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("📊 Status", callback_data='status'),
         InlineKeyboardButton("⚙️ Settings", callback_data='settings')],
        [InlineKeyboardButton("📈 Analytics", callback_data='analytics'),
         InlineKeyboardButton("❓ Help", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def send_message_to_channel(context: CallbackContext, text: str) -> None:
    """Utility function to send a message to the target channel."""
    try:
        await context.bot.send_message(
            chat_id=TARGET_CHAT_ID,
            text=text
        )
    except Exception as e:
        logger.error(f"Failed to send message to channel: {str(e)}")

async def error_handler(update: object, context: CallbackContext) -> None:
    """Handle errors."""
    logger.error(f"Exception while handling an update: {context.error}")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler('start', start))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Message and channel post handlers
    application.add_handler(MessageHandler(
        filters.TEXT | filters.COMMAND | filters.ChatType.CHANNEL,
        handle_message
    ))
    
    # Error handler
    application.add_error_handler(error_handler)

    try:
        logger.info(f"Starting bot for chat_id: {TARGET_CHAT_ID}")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, initiating shutdown...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot stopped")

if __name__ == '__main__':
    main()
