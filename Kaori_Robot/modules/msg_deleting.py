

import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from Kaori_Robot import dispatcher, LOGGER
from Kaori_Robot.modules.helper_funcs.chat_status import user_admin, can_delete, user_can_delete
from Kaori_Robot.modules.log_channel import loggable

from Kaori_Robot.modules.translations.strings import tld


@user_admin
@user_can_delete
@loggable
def purge(update, context) -> str:
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    args = context.args
    if msg.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            message_id = msg.reply_to_message.message_id
            delete_to = msg.message_id - 1
            if args and args[0].isdigit():
                new_del = message_id + int(args[0])
                # No point deleting messages which haven't been written yet.
                if new_del < delete_to:
                    delete_to = new_del

            for m_id in range(delete_to, message_id - 1, -1):  # Reverse iteration over message ids
                try:
                    bot.deleteMessage(chat.id, m_id)
                except BadRequest as err:
                    if err.message != "Message to delete not found":
                        LOGGER.exception("Error while purging chat messages.")

            try:
                msg.delete()
            except BadRequest as err:
                if err.message != "Message to delete not found":
                    LOGGER.exception("Error while purging chat messages.")

            bot.send_message(chat.id, tld(chat.id, "Purge complete."))
            return "<b>{}:</b>" \
                   "\n#PURGE" \
                   "\n<b>Admin:</b> {}" \
                   "\nPurged <code>{}</code> messages.".format(html.escape(chat.title),
                                                               mention_html(user.id, user.first_name),
                                                               delete_to - message_id)

    else:
        msg.reply_text(tld(chat.id, "Reply to a message to select where to start purging from."))

    return ""


@user_admin
@user_can_delete
@loggable
def del_message(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    if update.effective_message.reply_to_message:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        if can_delete(chat, bot.id):
            update.effective_message.reply_to_message.delete()
            update.effective_message.delete()
            return "<b>{}:</b>" \
                   "\n#DEL" \
                   "\n<b>Admin:</b> {}" \
                   "\nMessage deleted.".format(html.escape(chat.title),
                                               mention_html(user.id, user.first_name))
    else:
        update.effective_message.reply_text(tld(chat.id, "Whadya want to delete?"))

    return ""


__help__ = """
Need to delete lots of messages? That's what purges are for!

Available commands are:
 - /purge: deletes all messages from the message you replied to, to the current message.
 - /purge X: deletes X messages after the message you replied to (including the replied message)
 - /del: deletes the message you replied to.
"""

__mod_name__ = "Purges"

DELETE_HANDLER = CommandHandler("del", del_message, filters=Filters.chat_type.groups, run_async=True)
PURGE_HANDLER = CommandHandler("purge", purge, filters=Filters.chat_type.groups, pass_args=True, run_async=True)

dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(PURGE_HANDLER)
