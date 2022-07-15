"""Opens AIOgram listener, admin tracker, and Outline API;
Answers messages sent through the Telegram bot corresponding to ENV TELEGRAM_API_TOKEN"""

import os   # For signal (graceful shutdown)
import signal   # For graceful shutdown
import logging  # Logging important events
#import asyncio  # For sleep()
#from datetime import datetime
from types import NoneType   # Subscription checks
from aiogram import Bot, Dispatcher, executor, types  # Telegram API
from aiogram.types.message import ParseMode
#from aiogram import utils as aioutils
#from aiogram.types import InputFile
from dotenv import load_dotenv  # API tokens are stored in the .env file
### Admin broadcast deps START
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
### Admin broadcast deps END
from urllib3 import disable_warnings as disable_insecure_https_warnings
import markup as nav    # Bot menus
import btntext   # Telegram bot button text
import replies   # Telegram bot information output
import admin as admin_python     # Administration control
import outline as outline_api

# Logging
# Create a logger instance
log = logging.getLogger('main.py-aiogram')

# Create log formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Сreate console logging handler and set its level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)

# Create file logging handler and set its level
fh = logging.FileHandler(r'main.py.log')
fh.setFormatter(formatter)
log.addHandler(fh)

# Set logging level
match os.getenv('LOGGING_LEVEL').lower():
    case 'debug':
        log.setLevel(logging.DEBUG)
        log.critical("Log level set to debug")
    case 'info':
        log.setLevel(logging.INFO)
        log.critical("Log level set to info")
    case 'warning':
        log.setLevel(logging.WARNING)
        log.critical("Log level set to warning")
    case 'error':
        log.setLevel(logging.ERROR)
        log.critical("Log level set to error")
    case 'critical':
        log.setLevel(logging.CRITICAL)
        log.critical("Log level set to critical")

# Check if we are under Docker
DOCKER_MODE = False
if os.getenv("DOCKER_MODE") == 'true':
    DOCKER_MODE = True
    log.warning("Docker mode enabled")

# Load variables from .env
if not DOCKER_MODE:
    load_dotenv()

# Add user State
class StateCreateUser(StatesGroup):
    state_create_user = State()

# Delete user State
class StateDeleteUser(StatesGroup):
    state_delete_user = State()

# Authorization user State
class StateUserAuthorization(StatesGroup):
    state_user_authorization = State()

# Get Access URL State
class StateGetAccessURL(StatesGroup):
    state_get_access_url = State()

# # Admin handling (user expiration)
# class AdminStateExpiration(StatesGroup):
#     telegram_id = State()
#     expiration_date = State()
# admin_set_expiration_tgid = ''

# Disable insecure HTTPS warnings
disable_insecure_https_warnings()

# Load Outline API Manager
outline = outline_api.OutlineAPI(os.getenv('OUTLINE_SERVER'),
                                 os.getenv('OUTLINE_API_PORT'),
                                 os.getenv('OUTLINE_API_TOKEN'))

# System handling
class GracefulKiller:
    """Watches for SIGTERM and SIGKILL signals;
    if received, exits gracefully"""
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        """Exits gracefully"""
        exit(0)

# Get Telegram API token
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Initialize administration control
admin = admin_python.AdminTracker(os.getenv("ADMIN_SECRET"), docker_mode=True)

# Bot menu and replies
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message) -> None:
    """Sends welcome message and inits user's record in DB"""
    await message.reply(replies.welcome_message(message.from_user.first_name),
                        reply_markup=nav.notAuthorizedMenu)

def get_usernames_str() -> str:
        usernames = outline.get_key_names()
        usernames_str = ""
        for username in usernames:
            usernames_str += username
            usernames_str += '\n'
        return usernames_str

@dp.message_handler(commands=['help'])
async def send_help(message: types.Message) -> None:
    """Sends help message"""
    await message.reply(replies.help_message(), reply_markup=nav.mainMenu)

# Command handling
@dp.message_handler()
async def answer(message: types.Message) -> None:
    """Answers to random messages and messages from buttons"""
    # Menues
    if message.text == btntext.ENTER_SECURITY_CODE:
        await bot.send_message(message.from_user.id,
                               replies.ask_for_security_code(),
                               reply_markup=nav.notAuthorizedMenu)
        await StateUserAuthorization.state_user_authorization.set()

    elif not admin.is_admin(str(message.from_user.id)):
        await bot.send_message(message.from_user.id,
                               replies.user_not_authorized(),
                               reply_markup=nav.notAuthorizedMenu)
        return None

    if message.text == btntext.CREATE_USER:
        await bot.send_message(message.from_user.id,
                               replies.ask_for_new_user_name(),
                               reply_markup=nav.mainMenu)
        await StateCreateUser.state_create_user.set()
        log.debug(f"{message.from_user.id}: Create user access granted")
    
    elif message.text == btntext.DELETE_USER:
        await StateDeleteUser.state_delete_user.set()
        await bot.send_message(message.from_user.id,
                               replies.ask_for_username_to_delete(),
                               reply_markup=nav.mainMenu)
        await bot.send_message(message.from_user.id,
                               get_usernames_str(),
                               reply_markup=nav.mainMenu)

    # Main menu buttons
    elif message.text == btntext.GET_ACCESS_URL:
        await StateGetAccessURL.state_get_access_url.set()
        await bot.send_message(message.from_user.id,
                               replies.get_access_url_ask_for_username(),
                               reply_markup=nav.mainMenu)
        await bot.send_message(message.from_user.id,
                               get_usernames_str(),
                               reply_markup=nav.mainMenu)

    elif message.text == btntext.ENTER_SECURITY_CODE:
        # Set state
        await StateCreateUser.state_create_user.set()
        # Ask the user for the secret code
        await message.reply(replies.ask_for_security_code())
    
    elif message.text == btntext.MAIN_INSTRUCTIONS:
        await bot.send_message(message.from_user.id,
                               replies.instructions(),
                               reply_markup=nav.inlInstructionsKb)
        log.debug(f"{message.from_user.id}: Opened instructions menu")

    else:
        # Handle everything else
        if admin.is_admin(str(message.from_user.id)):
            reply_markup = nav.mainMenu
        else:
            reply_markup = nav.notAuthorizedMenu
        await bot.send_message(message.from_user.id,
                            replies.user_unknown_command(message.text),
                            reply_markup=reply_markup)
        log.debug(f"{message.from_user.id}: Sent an unknown command: {message.text}")


# Unauthorized user handling
@dp.message_handler(state=StateUserAuthorization.state_user_authorization)
async def add_user_to_admins(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    if admin.add(str(message.from_user.id), message.text):
        await bot.send_message(message.from_user.id,
                               replies.inform_admin(),
                               reply_markup=nav.mainMenu)
        return None
    await bot.send_message(message.from_user.id,
                           replies.inform_not_admin(),
                           reply_markup=nav.notAuthorizedMenu)

@dp.message_handler(state=StateCreateUser.state_create_user)
async def outline_create_new_user(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    if outline.create_user(message.text):
        await bot.send_message(message.from_user.id,
                               replies.user_created(message.text),
                               reply_markup=nav.mainMenu)
    else:
        await bot.send_message(message.from_user.id,
                               replies.user_not_created(message.text),
                               reply_markup=nav.mainMenu)

@dp.message_handler(state=StateDeleteUser.state_delete_user)
async def outline_delete_user(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    outline.delete_user(message.text)
    await bot.send_message(message.from_user.id,
                            replies.user_deleted(message.text),
                            reply_markup=nav.mainMenu)

@dp.message_handler(state=StateGetAccessURL.state_get_access_url)
async def get_access_url(message: types.Message, state: FSMContext) -> None:
    await state.finish()
    access_url = outline.get_access_url(message.text)
    if access_url is not None:
        await bot.send_message(message.from_user.id,
                               access_url,
                               reply_markup=nav.mainMenu)
        return None
    await bot.send_message(message.from_user.id,
                           replies.user_not_found(message.text),
                           reply_markup=nav.mainMenu)


def run() -> None:
    log.info('Starting...')
    killer = GracefulKiller()
    log.info('Process manager is up')
    log.info('Starting aiogram...')
    executor.start_polling(dp, skip_updates=True)
    log.info('aiogram stopped successfully')
