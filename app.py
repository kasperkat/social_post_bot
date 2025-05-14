from typing import Final, Dict
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, TypeHandler, ApplicationHandlerStop, CallbackContext, ConversationHandler
from dotenv import load_dotenv
import asyncio
import random
import requests
import re
import os
import subprocess
import base64
import json
import tweepy
from instagrapi import Client


load_dotenv()

TOKEN: Final = os.getenv("TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME")
CREATOR_ID = os.getenv("CREATOR_ID")

if CREATOR_ID is not None:
    CREATOR_ID = int(CREATOR_ID)

print(f"TOKEN: {TOKEN}")
print(f"BOT_USERNAME: {BOT_USERNAME}")
print(f"CREATOR_ID: {CREATOR_ID}")


CONFIRMING = 0

pending_images = {}

TEMP_FOLDER = './img_tmp'


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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    if user_id not in pending_images:
        message_type: str = update.message.chat.type
        text: str = update.message.text
        response: str = handle_response(text)
        await update.message.reply_text(response)
        print('Done')
        return
    
    text = update.message.text.lower()
    
    if text == 'yes':
        image_info = pending_images[user_id]
        file_path = image_info['file_path']
        caption = image_info['caption']
        


        # Handle the posting here
        to_x(file_path, caption)
        to_insta(file_path, caption)
        
        

        print('out')



        await update.message.reply_text(
            f"Image posted to Instagram with caption: \"{caption}\"", 
            reply_markup=ReplyKeyboardRemove()
        )
    elif text == 'no':
        await update.message.reply_text(
            "Image post cancelled.", 
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text("Please select Yes or No from the keyboard.")
        return
    
    file_path = pending_images[user_id]['file_path']
    if os.path.exists(file_path):
        os.remove(file_path)
    
    del pending_images[user_id]


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


async def whitelist_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != CREATOR_ID or update.message.chat.type != 'private':
        raise ApplicationHandlerStop


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    caption = update.message.caption if update.message.caption else ""
    user_id = update.effective_user.id

    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)

    file_path = os.path.join(TEMP_FOLDER, f"{file.file_id}.jpeg")
    await file.download_to_drive(file_path)
    
    pending_images[user_id] = {
        'file_path': file_path,
        'caption': caption
    }
    
    reply_keyboard = [['Yes', 'No']]
    markup = ReplyKeyboardMarkup(
        reply_keyboard, 
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        f'Do you want to post this image with the text: "{caption}"?',
        reply_markup=markup
    )







bearer_token = os.getenv("X_BEARER_TOKEN")
consumer_key = os.getenv("X_API_KEY")
consumer_secret = os.getenv("X_API_SECRET")
access_token = os.getenv("X_ACCESS_TOKEN")
access_token_secret = os.getenv("X_ACCESS_SECRET")

# Authenticate Twitter API
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, wait_on_rate_limit=True)

client = tweepy.Client(
    bearer_token,
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret,
    wait_on_rate_limit=True,
)

def to_x(img_path: str, tweet_text: str):
    """Posts an image and text to Twitter (X)."""
    try:
        # Upload image to Twitter
        media_id = api.media_upload(filename=img_path).media_id_string

        # Post Tweet with text and image
        response = client.create_tweet(text=tweet_text, media_ids=[media_id])
        print(f"Tweeted! Tweet ID: {response.data['id']}")

    except Exception as e:
        print(f"Error posting tweet: {e}")








SESSION_FILE = "insta_session.json"

USERNAME = os.getenv("IG_USER")
PASSWORD = os.getenv("IG_PASSWORD")

def login_to_instagram():
    """Logs into Instagram or restores an existing session."""
    client = Client()

    # Load saved session if available
    if os.path.exists(SESSION_FILE):
        client.load_settings(SESSION_FILE)
        try:
            # Verify session is still valid
            client.get_timeline_feed()
            print("✅ Session restored successfully!")
            return client
        except:
            print("⚠️ Session expired, logging in again...")

    # If session is invalid, perform a new login
    client.login(USERNAME, PASSWORD)

    # Save session for future use
    client.dump_settings(SESSION_FILE)
    print("🔄 New session saved!")

    return client

def to_insta(image_path, caption):
    """Posts an image without requiring login every time."""
    client = login_to_instagram()
    media = client.photo_upload(image_path, caption)
    return f"✅ Posted successfully to Insta! Media ID: {media.dict().get('id')}"










def run_telebot():
    print("Starting bot")
    app = Application.builder().token(TOKEN).build()
    filter_users = TypeHandler(Update, whitelist_users)
    app.add_handler(filter_users, -1)

    command_handler = MessageHandler(filters.COMMAND, handler_command)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    image_handler = MessageHandler(filters.PHOTO, handle_image)

    handlers = [command_handler, message_handler, image_handler]

    for handler in handlers:
        app.add_handler(handler)

    user_states = {}
    app.context_types.context.user_states = user_states
    print("Listening...")
    app.run_polling()


if __name__ == '__main__':
    run_telebot()