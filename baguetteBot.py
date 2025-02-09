"""
This bot is used for a community to stay updated for the
baguette flavours of each day. A person must visit the Bitti cafe
and update the bot by /add command.
"""
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import random

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
baguettes = [] # List of (flavour, date) tuples

ALLOWED_GROUPS = {-1002468965180, 5978668914} #The baguette group


global_message_count = 0
FLOOD_LIMIT = 10  # Max messages per minute
FLOOD_RESET_TIME = 60  # Seconds before reset
flood_block_until = None


def flood_protection(func):
    """Blocks bot if too many messages arrive globally."""
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        global global_message_count, flood_block_until
        now = datetime.now()

        if flood_block_until and now < flood_block_until:
            return  # Ignore messages while flood block is active

        global_message_count += 1
        if global_message_count >= FLOOD_LIMIT:
            flood_block_until = now + timedelta(seconds=FLOOD_RESET_TIME)
            global_message_count = 0  # Reset counter
            return  # Ignore the message

        return func(update, context, *args, **kwargs)

    return wrapper


FACT_FILE = "faktat.txt"
daily_fact = None


@flood_protection
def daily_baguette_fact(update: Update, context: CallbackContext) -> None:
    """
    Remember to update to reset daily_fact to None.
    """
    global daily_fact

    if daily_fact is not None:
        update.message.chat.send_message("Päivän fakta on jo jaettu! Yritä huomenna uudestaan. 🥖😱")
        return

    with open(FACT_FILE, "r", encoding="utf-8") as file:
        facts = file.readlines()

    if not facts:
        update.message.chat.send_message("Ei löytynyt yhtään patonki-faktaa! 🥖😱")
        return

    daily_fact = random.choice(facts).strip()
    today = datetime.now().strftime("%d.%m.%Y")
    update.message.chat.send_message(f"Päivän fakta ({today})🥖😱:\n{daily_fact}")


def group_restricted(func):
    """
    Currently only allows one group and dev
    """
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        chat_id = update.effective_chat.id
        if chat_id not in ALLOWED_GROUPS:
            update.message.chat.send_message("Nope!")
            return
        return func(update, context, *args, **kwargs)
    return wrapper


@flood_protection
@group_restricted
def start(update: Update, context: CallbackContext) -> None:
    update.message.chat.send_message("Hei, olen PatonkiBotti \n"
                              "Komennot:\n"
                              "/add [patonki]\n/del [numero]\n/list\n/delall\n/fact")


def remove_old_baguettes():
    """Removes baguettes from the previous day."""
    today = datetime.now().strftime("%d.%m.%Y")
    global baguettes
    baguettes = [(flavour, date) for flavour, date in baguettes if date == today]


@flood_protection
@group_restricted
def add_baguette(update: Update, context: CallbackContext) -> None:
    """/add [flavour]"""
    if not context.args:
        update.message.chat.send_message("Käytä: /add [patonki]")
        return

    remove_old_baguettes()  # Clean up old baguettes first
    flavours = " ".join(context.args).split(",")
    flavours = [flavour.strip() for flavour in flavours]
    today = datetime.now().strftime("%d.%m.%Y")

    #Add to baguette to history to collect data
    with open("history.txt", "a", encoding="utf-8") as file:
        for flavour in flavours:
            file.write(f"{today}: {flavour}")
            baguettes.append((flavour, today))

    update.message.chat.send_message(f"Lisättiin patongit: {', '.join(flavours)} ({today})")


@flood_protection
@group_restricted
def del_baguette(update: Update, context: CallbackContext) -> None:
    if not context.args or not context.args[0].isdigit():
        update.message.chat.send_message("Käytä: /del [patonki numero]")
        return

    try:
        index = int(context.args[0]) - 1
    except ValueError:
        update.message.chat.send_message("Virheellinen numero! Käytä: /del [numero]")
        return

    remove_old_baguettes()  # Clean up before deleting

    if 0 <= index < len(baguettes):
        removed, _ = baguettes.pop(index)
        update.message.chat.send_message(f"Poistettiin patonki #{index + 1}: {removed}")
    else:
        update.message.chat.send_message("Väärä patonki numero.")


@flood_protection
def list_baguettes(update: Update, context: CallbackContext) -> None:
    remove_old_baguettes()
    today = datetime.now().strftime("%d.%m.%Y")

    if baguettes:
        message = f"Patongit ({today}):\n" + "\n".join(
            [f"{i + 1}. {b[0]}" for i, b in enumerate(baguettes)])
    else:
        message = f"Patongit ({today}): Ei patonkeja :("

    update.message.chat.send_message(message)


@flood_protection
@group_restricted
def del_all_baguettes(update: Update, context: CallbackContext) -> None:
    global baguettes
    if baguettes:
        baguettes.clear()  # Clears the list
        update.message.chat.send_message("Kaikki patongit poistettu!")
    else:
        update.message.chat.send_message("Ei patonkeja poistettavaksi.")


def error_handler(update: Update, context: CallbackContext) -> None:
    """Logs errors and notifies the user."""
    print(f"Error: {context.error}")
    update.message.chat.send_message("Hups! Tapahtui virhe.")


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_baguette))
    dp.add_handler(CommandHandler("del", del_baguette))
    dp.add_handler(CommandHandler("list", list_baguettes))
    dp.add_handler(CommandHandler("delall", del_all_baguettes))
    dp.add_handler(CommandHandler("fact", daily_baguette_fact))
    dp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()