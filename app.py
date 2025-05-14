from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, TypeHandler, ApplicationHandlerStop, CallbackContext
from dotenv import load_dotenv
from typing import Final
import asyncio
import random
import requests
import re
import os
import subprocess
import base64
import json


load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
CREATOR_ID = os.getenv("CREATOR_ID")

if CREATOR_ID is not None:
    CREATOR_ID = int(CREATOR_ID)

print(f"TOKEN: {TOKEN}")
print(f"BOT_USERNAME: {BOT_USERNAME}")
print(f"CREATOR_ID: {CREATOR_ID}")



def handle_response(text: str) ->str:

    processed: str = text.lower()

    if 'hello' == processed:
        return 'Hey there!'
    
    return "I literally can't even answer that"



async def start_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm Toga!")




async def handler_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command_functions = {
        '/start': start_function,

    }

    if update.message.text not in command_functions:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="I dont know how to do that!")
    else:
        await command_functions[update.message.text](update, context)





async def handle_message( update: Update, context: ContextTypes.DEFAULT_TYPE ):

    message_type: str = update.message.chat.type
    text: str = update.message.text

    response: str = handle_response( text )

    await update.message.reply_text(response)
        
    print('Done')




async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print( f'Update {update} caused error {context.error}' )



async def whitelist_users( update: Update, context: ContextTypes.DEFAULT_TYPE ):
    if( update.effective_chat.id != CREATOR_ID or update.message.chat.type != 'private' ):
        # await update.effective_message.reply_text('ayo', reply_to_message)
        raise ApplicationHandlerStop







TEMP_FOLDER = './img_tmp'


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file = await context.bot.get_file(update.message.photo[-1].file_id)
    caption = update.message.caption if update.message.caption else ""

    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)

    file_path = os.path.join(TEMP_FOLDER, f"{file.file_id}.jpeg")
    await file.download_to_drive(file_path)



    to_insta( file_path, caption )



    await update.message.reply_text(f'Got your image with a caption: "{caption}"')

    os.remove(file_path)






def run_telebot():
    print("Starting bot")
    app = Application.builder().token( TOKEN ).build()
    filter_users = TypeHandler(Update, whitelist_users)
    app.add_handler( filter_users, -1 )

    command_handler = MessageHandler(filters.COMMAND, handler_command)
    message_handler = MessageHandler( filters.TEXT & ( ~filters.COMMAND ), handle_message )
    image_handler = MessageHandler(filters.PHOTO, handle_image)

    handlers = [ command_handler, message_handler,  image_handler ]

    for handler in handlers:
        app.add_handler(handler)

    user_states = {}
    app.context_types.context.user_states = user_states
    print("Listening...")
    app.run_polling()










def to_insta( img_path, post_caption ):
    print('Posting in Insta')
    return




if __name__ == '__main__':

    run_telebot()




