"""Handles Telegram bot button creation and mapping"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import btntext


# Not authorized menu
btnNotAuthorized = KeyboardButton(btntext.NOT_AUTHORIZED)
btnEnterSecurityCode = KeyboardButton(btntext.ENTER_SECURITY_CODE)
notAuthorizedMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnNotAuthorized, btnEnterSecurityCode)

# Main menu
btnAddUser = KeyboardButton(btntext.CREATE_USER)
btnDelUser = KeyboardButton(btntext.DELETE_USER)
btnGetAccessURL = KeyboardButton(btntext.GET_ACCESS_URL)
BtnInstructions = KeyboardButton(btntext.MAIN_INSTRUCTIONS)
mainMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnAddUser,
                                                         btnDelUser,
                                                         BtnInstructions,
                                                         btnGetAccessURL)


# Inline instructions menu
inlInstructionsBtn1 = InlineKeyboardButton(btntext.INL_INST_IOS,
                                           callback_data=btntext.INL_INST_IOS)
inlInstructionsBtn2 = InlineKeyboardButton(btntext.INL_INST_ANDROID,
                                           callback_data=btntext.INL_INST_ANDROID)
inlInstructionsKb = InlineKeyboardMarkup(row_width=2).add(inlInstructionsBtn1,
                                                          inlInstructionsBtn2)
