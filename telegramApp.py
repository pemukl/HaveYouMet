from typing import Optional

from telegram import Update, InputMediaDocument, InputMediaPhoto
from typing import DefaultDict, Optional, Set
from collections import defaultdict
from telegram.constants import ParseMode
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext, \
    ExtBot, Application, TypeHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

from game import Challenge, Player, Game


class ChatData:
    """Custom class for chat_data. Here we store data per message."""

    def __init__(self) -> None:
        self.clicks_per_message: DefaultDict[int, int] = defaultdict(int)

        self.challenges = {}


# The [ExtBot, dict, ChatData, dict] is for type checkers like mypy
class CustomContext(CallbackContext[ExtBot, dict, ChatData, dict]):
    """Custom class for context."""

    def __init__(self, application: Application, chat_id: int = None, user_id: int = None):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
        self._message_id: Optional[int] = None

    @property
    def player(self):
        """Custom shortcut to access a value stored in the bot_data dict"""
        global config
        game = Game(config)
        player = game.get_player(self._user_id)
        return player



    @property
    def challenge(self) -> Optional[Challenge]:
        """Access the number of clicks for the message this context object was built for."""
        if self._message_id:
            return self.chat_data.challenges[self._message_id]
        return None

    @challenge.setter
    def challenge(self, value: Challenge) -> None:
        """Allow to change the challenge"""
        if not self._message_id:
            raise RuntimeError("There is no message associated with this context object.")
        self.chat_data.challenges[self._message_id] = value

    @classmethod
    def from_update(cls, update: object, application: "Application") -> "CustomContext":
        """Override from_update to set _message_id."""
        # Make sure to call super()
        context = super().from_update(update, application)

        if context.chat_data and isinstance(update, Update) and update.effective_message:
            context._message_id = update.effective_message.message_id
        return context


def text_from_challenge(challenge: Challenge,index):
    emoji = "✅" if challenge.picked[index] == 1 else ("❌" if challenge.picked[index] == -1 else " ")
    text=emoji + " " + challenge.options[index].name + " " + emoji
    return text

def button_from_challenge(challenge: Challenge, index):
    but = InlineKeyboardButton(text=text_from_challenge(challenge,index), callback_data=index)
    return but


def keyboard_from_challenge(challenge: Challenge):
    keyboard = [
        [
            button_from_challenge(challenge, 0),
            button_from_challenge(challenge, 1),
        ],
        [
            button_from_challenge(challenge, 2),
            button_from_challenge(challenge, 3),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

async def start(update: Update, context: CustomContext) -> None:
    """Display a message with a button."""
    player = context.player
    challenge = player.generate_challenge()
    ret = await context.bot.sendPhoto(chat_id=update.effective_chat.id,
                                photo=open(challenge.get_image_path(), 'rb'),
                                caption="Who is this?",
                                reply_markup=keyboard_from_challenge(challenge))

    context.chat_data.challenges[ret.message_id] = challenge


async def answer_click(update: Update, context: CustomContext) -> None:
    """Rect to click."""
    await update.callback_query.answer()
    choosen = int(update.callback_query.data)
    if context.challenge.picked[choosen] == 0:
        if context.challenge.pick_option(choosen):
            context.challenge = context.player.generate_challenge()
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(media=open(context.challenge.get_image_path(), 'rb'),
                    caption="Score: " + str(context.player.score()) + " 🚀",),
            reply_markup=keyboard_from_challenge(context.challenge)
        )



async def print_users(update: Update, context: CustomContext) -> None:
    """Show which users have been using this bot."""
    await update.message.reply_text(
        "The following user IDs have used this bot: "
        f'{", ".join(map(str, context.bot_user_ids))}'
    )





class TelegramApp:

    def __init__(self, conf):
        global config
        config = conf

    def run(self):
        global config
        context_types = ContextTypes(context=CustomContext, chat_data=ChatData)
        application = Application.builder().token(config["botToken"]).context_types(
            context_types).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(answer_click))
        application.run_polling()
