"""
This example shows how to use webhook on behind of any reverse proxy (nginx, traefik, ingress etc.)
"""
import asyncio
import logging
import sys

from aiohttp import web

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import os
from dotenv import load_dotenv

load_dotenv()
# Bot token can be obtained via https://t.me/BotFather
debug = int(os.environ.get("DEBUG"))
TOKEN = os.environ.get('TELEGRAM_TOKEN')
NGINX_HOST = os.environ.get('NGINX_HOST')

# Webserver settings
# bind localhost only to prevent any external access
WEB_SERVER_HOST = "0.0.0.0"
# Port for incoming request from reverse proxy. Should be any available port
WEB_SERVER_PORT = 3001

# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = "/webhook"
# Secret key to validate requests from Telegram (optional)
WEBHOOK_SECRET = "my-secret"
# Base URL for webhook will be used to generate webhook URL for Telegram,
# in this example it is used public DNS with HTTPS support
BASE_WEBHOOK_URL = f"https://{NGINX_HOST}"

# All handlers should be attached to the Router (or Dispatcher)

router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {hbold(message.from_user.full_name)}!")


@router.message()
async def echo_handler(message: types.Message) -> None:
    """
    Handler will forward receive a message back to the sender
    By default, message handler will handle all message types (like text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def on_startup(bot: Bot) -> None:
    # If you have a self-signed SSL certificate, then you will need to send a public
    # certificate to Telegram
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)
    print(f'Telegram servers now send updates to {BASE_WEBHOOK_URL}. Bot is online')


def main() -> None:
    dp = Dispatcher()
    dp.include_router(router)

    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)

    dp.startup.register(on_startup)
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


async def main_polling() -> None:
    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await bot.delete_webhook()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    if debug:
        asyncio.run(main_polling())
    else:
        main()
