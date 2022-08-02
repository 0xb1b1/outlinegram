"""Opens AIOgram listener, admin tracker, and Outline API;
Answers messages sent through the Telegram bot corresponding to ENV TELEGRAM_API_TOKEN"""

# region Dependencices
import os   # For signal (graceful shutdown)
import signal   # For graceful shutdown
import logging  # Logging important events
from types import NoneType   # Subscription checks
from aiogram import Bot, Dispatcher, executor, types  # Telegram API
from aiogram.types.message import ParseMode
from dotenv import load_dotenv  # API tokens are stored in the .env file
# States
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from urllib3 import disable_warnings as disable_insecure_https_warnings
# .py files
import markup as nav    # Bot menus
import btntext          # Telegram bot button text
import replies          # Telegram bot information output
import admin as admin_python     # Administration control
import outline as outline_api    # Outline Server management
# endregion

# region Logging
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
fh = logging.FileHandler(r'bot.py.log')
fh.setFormatter(formatter)
log.addHandler(fh)

# Set logging level
# Set logging level
# TODO: Convert back to match-case when pylint implements .this
logging_level_lower = os.getenv('LOGGING_LEVEL').lower()
if logging_level_lower == 'debug':
    log.setLevel(logging.DEBUG)
    log.critical("Log level set to debug")
elif logging_level_lower == 'info':
    log.setLevel(logging.INFO)
    log.critical("Log level set to info")
elif logging_level_lower == 'warning':
    log.setLevel(logging.WARNING)
    log.critical("Log level set to warning")
elif logging_level_lower == 'error':
    log.setLevel(logging.ERROR)
    log.critical("Log level set to error")
elif logging_level_lower == 'critical':
    log.setLevel(logging.CRITICAL)
    log.critical("Log level set to critical")
# endregion

# Check if we are under Docker
DOCKER_MODE = False
if os.getenv("DOCKER_MODE") == 'true':
    DOCKER_MODE = True
    log.warning("Docker mode enabled")

# Load variables from .env
if not DOCKER_MODE:
    load_dotenv()


# region AIOgramDispatcherStates
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
# endregion


# Disable insecure HTTPS warnings
disable_insecure_https_warnings()

# Load Outline API Manager
outline = outline_api.OutlineAPI(os.getenv('OUTLINE_SERVER'),
                                 os.getenv('OUTLINE_API_PORT'),
                                 os.getenv('OUTLINE_API_TOKEN'))

# Get Telegram API token
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Initialize administration control
admin = admin_python.AdminTracker(os.getenv("ADMIN_SECRET"), docker_mode=DOCKER_MODE)


# region CustomFunctions
def get_usernames_str() -> str:
        usernames = outline.get_key_names()
        usernames_str = ""
        for username in usernames:
            usernames_str += username
            usernames_str += '\n'
        return usernames_str
# endregion


# region BotReplies
# Command message handling
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message) -> None:
    """Sends welcome message and inits user's record in DB"""
    await message.reply(replies.welcome_message(message.from_user.first_name),
                        reply_markup=nav.notAuthorizedMenu)


@dp.message_handler(commands=['help'])
async def send_help(message: types.Message) -> None:
    """Sends help message"""
    await message.reply(replies.help_message(), reply_markup=nav.mainMenu)


# Normal message handling
@dp.message_handler()
async def answer(message: types.Message) -> None:
    """Answers to random messages and messages from buttons"""
    # Menus
    if message.text == btntext.ENTER_SECURITY_CODE:
        await bot.send_message(message.from_user.id,
                               replies.ask_for_security_code(),
                               reply_markup=nav.notAuthorizedMenu)
        await StateUserAuthorization.state_user_authorization.set()
        return None

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

    # Handle everything else
    else:
        if admin.is_admin(str(message.from_user.id)):
            reply_markup = nav.mainMenu
        else:
            reply_markup = nav.notAuthorizedMenu
        await bot.send_message(message.from_user.id,
                               replies.user_unknown_command(message.text),
                               reply_markup=reply_markup)
        log.debug(f"{message.from_user.id}: Sent an unknown command: {message.text}")


## State messages handling
# Unauthorized user
@dp.message_handler(state=StateUserAuthorization.state_user_authorization)
async def add_user_to_admins(message: types.Message, state: FSMContext) -> None:
    """Adds user to administrator list if their key matches ADMIN_SECRET"""
    await state.finish()
    if admin.add(str(message.from_user.id), message.text):
        await bot.send_message(message.from_user.id,
                               replies.inform_admin(),
                               reply_markup=nav.mainMenu)
        return None
    await bot.send_message(message.from_user.id,
                           replies.inform_not_admin(),
                           reply_markup=nav.notAuthorizedMenu)


# User creation
@dp.message_handler(state=StateCreateUser.state_create_user)
async def outline_create_user(message: types.Message, state: FSMContext) -> None:
    """Creates new Outline server username"""
    await state.finish()
    if outline.create_user(message.text):
        await bot.send_message(message.from_user.id,
                               replies.user_created(message.text),
                               reply_markup=nav.mainMenu)
    else:
        await bot.send_message(message.from_user.id,
                               replies.user_not_created(message.text),
                               reply_markup=nav.mainMenu)


# User removal
@dp.message_handler(state=StateDeleteUser.state_delete_user)
async def outline_delete_user(message: types.Message, state: FSMContext) -> None:
    """Removes Outline Server username from the server"""
    await state.finish()
    outline.delete_user(message.text)
    await bot.send_message(message.from_user.id,
                           replies.user_deleted(message.text),
                           reply_markup=nav.mainMenu)


# User Access URL retrieval
@dp.message_handler(state=StateGetAccessURL.state_get_access_url)
async def get_access_url(message: types.Message, state: FSMContext) -> None:
    """Gets Outline Server Access URL by username"""
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
# endregion


# region StartUp
def run() -> None:
    log.info('Starting...')
    log.info('Starting AIOgram...')
    executor.start_polling(dp, skip_updates=True)
    log.info('AIOgram stopped successfully')
# endregion
