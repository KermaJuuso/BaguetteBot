"""
This bot is used for a community to stay updatet for the
baguette flavours of each day. A person must visit the Bitti cafe
and update the bot by /add command.
"""
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
baguettes = [] # List of (flavour, date) tuples

ALLOWED_GROUPS = {-1002468965180, 5978668914} #The baguette group


def group_restricted(func):
    """
    Currently only allows one group and dev
    """
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        chat_id = update.effective_chat.id
        if chat_id not in ALLOWED_GROUPS:
            update.message.reply_text("Nope!")
            return
        return func(update, context, *args, **kwargs)
    return wrapper


@group_restricted
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Hei, olen PatonkiBotti \n"
                              "Komennot:\n"
                              "/add [patonki]\n/del [numero]\n/list\n/delall")


def remove_old_baguettes():
    """Removes baguettes from the previous day."""
    today = datetime.now().date()
    global baguettes
    baguettes = [(flavour, date) for flavour, date in baguettes if date == today]


@group_restricted
def add_baguette(update: Update, context: CallbackContext) -> None:
    if not context.args:
        update.message.reply_text("Käytä: /add [patonki]")
        return

    remove_old_baguettes()  # Clean up old baguettes first

    flavour = " ".join(context.args)
    today = datetime.now().date()
    baguettes.append((flavour, today))
    update.message.reply_text(f"Lisättiin patonki #{len(baguettes)}: {flavour} ({today})")


@group_restricted
def del_baguette(update: Update, context: CallbackContext) -> None:
    if not context.args or not context.args[0].isdigit():
        update.message.reply_text("Käytä: /del [patonki numero]")
        return

    remove_old_baguettes()  # Clean up before deleting

    index = int(context.args[0]) - 1
    if 0 <= index < len(baguettes):
        removed, _ = baguettes.pop(index)
        update.message.reply_text(f"Poistettiin patoni #{index + 1}: {removed}")
    else:
        update.message.reply_text("Väärä patonki numero.")


@group_restricted
def list_baguettes(update: Update, context: CallbackContext) -> None:
    remove_old_baguettes()
    today = datetime.now().date()

    if baguettes:
        message = f"Patongit ({today}):\n" + "\n".join(
            [f"{i + 1}. {b[0]}" for i, b in enumerate(baguettes)])
    else:
        message = f"Patongit ({today}): Ei patonkeja :("

    update.message.reply_text(message)


@group_restricted
def del_all_baguettes(update: Update, context: CallbackContext) -> None:
    global baguettes
    if baguettes:
        baguettes.clear()  # Clears the list
        update.message.reply_text("Kaikki patongit poistettu!")
    else:
        update.message.reply_text("Ei patonkeja poistettavaksi.")


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add_baguette))
    dp.add_handler(CommandHandler("del", del_baguette))
    dp.add_handler(CommandHandler("list", list_baguettes))
    dp.add_handler(CommandHandler("delall", del_all_baguettes))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()