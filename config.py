import telebot
import configure
import sqlite3
import threading
import logging
from texts import LogsGID
# Initialize bot
client = telebot.TeleBot(configure.config['token'])

# Initialize database connection
db = sqlite3.connect('./MEGAVOID/MEGAVOID v0.7/mainDB.db', check_same_thread=False)
sql = db.cursor()

# Lock for threading
lock = threading.Lock()

# Global dictionary to store user sessions
user_sessions = {}

# Function to get the session for a user
def get_user_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {}  # Create a new session if not exist
        print(f"Created new session for user_id: {user_id}")

    session = user_sessions[user_id]
    print(f"Accessing session for user_id: {user_id}, session data: {session}")
    return session

# Function to clear the session after the order is completed
def clear_user_session(user_id):
    if user_id in user_sessions:
        del user_sessions[user_id]
        print(f"Cleared session for user_id: {user_id}")

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Telegram Group Logger
class TelegramLoggingHandler(logging.Handler):
    def __init__(self, bot, chat_id):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.bot.send_message(chat_id=self.chat_id, text=log_entry)
        except Exception as e:
            print(f"Failed to send log message to Telegram: {e}")

logs_gid = LogsGID
telegram_handler = TelegramLoggingHandler(client, logs_gid)
telegram_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
telegram_handler.setFormatter(formatter)
logger.addHandler(telegram_handler)

# Database setup
sql.execute("""CREATE TABLE IF NOT EXISTS users (id BIGINT, username TEXT, access INT, verified INT)""")
sql.execute("""CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)""")
sql.execute("""CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, caption TEXT, url TEXT, cbdata TEXT, category TEXT)""")
sql.execute("""CREATE TABLE IF NOT EXISTS verifications (id BIGINT, username TEXT, fullname TEXT, pnumber TEXT, address TEXT, verified INT, photo_message_id BIGINT, recipe_message_id BIGINT)""")
db.commit()
