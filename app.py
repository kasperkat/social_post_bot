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
from instagrapi import Client as IG_Client
from atproto import Client as ASK_Client, models

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
        posted_to_x = to_x(file_path, caption)
        posted_to_insta = to_insta(file_path, caption)
        posted_to_bluesky = to_bluesky(file_path, caption)
        

        msg = "Report:\n"
        if(posted_to_x):
            msg += "\n✔️ X"
        else:
            msg += "\n❌ X"


        if(posted_to_insta):
            msg += "\n✔️ Instagram"
        else:
            msg += "\n❌ Instagram"

        
        if(posted_to_bluesky):
            msg += "\n✔️ Bluesky"
        else:
            msg += "\n❌ Bluesky"




        await update.message.reply_text(
            f"{msg}", 
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
        return True

    except Exception as e:
        print(f"Error posting tweet: {e}")
        return False





SESSION_FILE = "insta_session.json"

USERNAME = os.getenv("IG_USER")
PASSWORD = os.getenv("IG_PASSWORD")

def login_to_instagram():
    """Logs into Instagram or restores an existing session."""
    client = IG_Client()

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

    media_id = media.dict().get('id')
    if media_id:
        return True
    else:
        return False





def to_bluesky(image_path, caption):
    BSKY_USERNAME = os.getenv("BSKY_USER")
    BSKY_PASSWORD = os.getenv("BSKY_PASSWORD")

    if not BSKY_USERNAME or not BSKY_PASSWORD:
        raise Exception("Bluesky credentials missing. Set BSKY_USER and BSKY_PASSWORD.")

    client = ASK_Client()
    
    try:
        client.login(BSKY_USERNAME, BSKY_PASSWORD)
    except Exception as e:
        raise Exception(f"Login failed: {e}")

    try:
        with open(image_path, "rb") as f:
            img_data = f.read()
        
        
        image_response = client.upload_blob(img_data)
        image_blob = image_response.blob

        
        embed = models.AppBskyEmbedImages.Main(
            images=[models.AppBskyEmbedImages.Image(
                alt=caption,
                image=image_blob
            )]
        )


        post = client.send_post(
            text=caption,
            embed=embed  
        )
        
        print("Post created successfully:", post.uri)
        return True

    except Exception as e:
        print(f"Image upload failed: {e}. No post was created.")
        return False



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