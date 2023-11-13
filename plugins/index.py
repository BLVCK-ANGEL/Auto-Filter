import logging
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS
from info import INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp
import re
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
lock = asyncio.Lock()


@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cᴀɴᴄᴇʟʟɪɴɢ Iɴᴅᴇxɪɴɢ")
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(int(from_user),
                               f'Yᴏᴜʀ sᴜʙᴍɪssɪᴏɴ ғᴏʀ ɪɴᴅᴇxɪɴɢ {chat} ʜᴀs ʙᴇᴇɴ ᴅᴇᴄʟɪᴇɴᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs.',
                               reply_to_message_id=int(lst_msg_id))
        return

    if lock.locked():
        return await query.answer('Wᴀɪᴛ ᴜɴᴛɪʟ ᴘʀᴇᴠɪᴏᴜs ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇ.', show_alert=True)
    msg = query.message

    await query.answer('Pʀᴏᴄᴇssɪɴɢ...⏳', show_alert=True)
    if int(from_user) not in ADMINS:
        await bot.send_message(int(from_user),
                               f'Yᴏᴜʀ sᴜʙᴍɪssɪᴏɴ ғᴏʀ ɪɴᴅᴇxɪɴɢ {chat} ʜᴀs ʙᴇᴇɴ ᴀᴄᴄᴇᴘᴛᴇᴅ ʙʏ ᴏᴜʀ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴀɴᴅ ᴡɪʟʟ ʙᴇ ᴀᴅᴅᴇᴅ sᴏᴏɴ.',
                               reply_to_message_id=int(lst_msg_id))
    await msg.edit(
        "Sᴛᴀʀᴛɪɴɢ Iɴᴅᴇxɪɴɢ",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Cᴀɴᴄᴇʟ', callback_data='index_cancel')]]
        )
    )
    try:
        chat = int(chat)
    except:
        chat = chat
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | (filters.regex("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Iɴᴠᴀʟɪᴅ ʟɪɴᴋ')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('Tʜɪs ᴍᴀʏ ʙᴇ ᴀ ᴘʀɪᴠᴀᴛᴇ Cʜᴀɴɴᴇʟ / Gʀᴏᴜᴘ. Mᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴏᴠᴇʀ ᴛʜᴇʀᴇ ᴛᴏ ɪɴᴅᴇx ᴛʜᴇ ғɪʟᴇs.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Iɴᴠᴀʟɪᴅ ʟɪɴᴋ sᴘᴇᴄɪғɪᴇᴅ.')
    except Exception as e:
        logger.exception(e)
        return await message.reply(f'Eʀʀᴏʀs - {e}')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('Mᴀᴋᴇ sᴜʀᴇ ᴛʜᴀᴛ I ᴀᴍ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ, ɪғ ᴄʜᴀɴɴᴇʟ ɪs ᴘʀɪᴠᴀᴛᴇ')
    if k.empty:
        return await message.reply('Tʜɪs ᴍᴀʏ ʙᴇ ɢʀᴏᴜᴘ ᴀɴᴅ ɪᴀᴍ ɴᴏᴛ ᴀ ᴀᴅᴍɪɴ ᴏғ ᴛʜᴇ ɢʀᴏᴜᴘ.')

    if message.from_user.id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton('Yᴇs ',
                                     callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
            ],
            [
                InlineKeyboardButton('Cʟᴏsᴇ', callback_data='close_data'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'Dᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɪɴᴅᴇx ᴛʜɪs Cʜᴀɴɴᴇʟ/ Gʀᴏᴜᴘ?\n\nCʜᴀᴛ ID/ Usᴇʀɴᴀᴍᴇ: <code>{chat_id}</code>\nLᴀsᴛ ᴍᴇssᴀɢᴇ ID: <code>{last_msg_id}</code>',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Mᴀᴋᴇ sᴜʀᴇ ɪᴀᴍ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ ᴀɴᴅ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ɪɴᴠɪᴛᴇ ᴜsᴇʀs.')
    else:
        link = f"@{message.forward_from_chat.username}"
    buttons = [
        [
            InlineKeyboardButton('Aᴄᴄᴇᴘᴛ Iɴᴅᴇx',
                                 callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')
        ],
        [
            InlineKeyboardButton('Rᴇᴊᴇᴄᴛ Iɴᴅᴇx',
                                 callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(LOG_CHANNEL,
                           f'#IndexRequest\n\nBʏ : {message.from_user.mention} (<code>{message.from_user.id}</code>)\nCʜᴀᴛ ID/ Usᴇʀɴᴀᴍᴇ - <code> {chat_id}</code>\nLᴀsᴛ ᴍᴇssᴀɢᴇ ID - <code>{last_msg_id}</code>\nIɴᴠɪᴛᴇ Lɪɴᴋ - {link}',
                           reply_markup=reply_markup)
    await message.reply('Tʜᴀɴᴋ Yᴏᴜ ғᴏʀ ᴛʜᴇ ᴄᴏɴᴛʀɪʙᴜᴛɪᴏɴ, Wᴀɪᴛ ғᴏʀ ᴍʏ ᴍᴏᴅᴇʀᴀᴛᴏʀs ᴛᴏ ᴠᴇʀɪғʏ ᴛʜᴇ ғɪʟᴇs.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Sᴋɪᴘ ɴᴜᴍʙᴇʀ sʜᴏᴜʟᴅ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.")
        await message.reply(f"Sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ SKIP ɴᴜᴍʙᴇʀ ᴀs {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("Gɪᴠᴇ ᴍᴇ ᴀ sᴋɪᴘ ɴᴜᴍʙᴇʀ")


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False
            async for message in bot.iter_messages(chat, lst_msg_id, temp.CURRENT):
                if temp.CANCEL:
                    await msg.edit(f"Successfully Cancelled!!\n\nSaved <code>{total_files}</code> files to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>")
                    break
                current += 1
                if current % 20 == 0:
                    can = [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
                    reply = InlineKeyboardMarkup(can)
                    await msg.edit_text(
                        text=f"Total messages fetched: <code>{current}</code>\nTotal messages saved: <code>{total_files}</code>\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>",
                        reply_markup=reply)
                if message.empty:
                    deleted += 1
                    continue
                elif not message.media:
                    no_media += 1
                    continue
                elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue
                media.file_type = message.media.value
                media.caption = message.caption
                aynav, vnay = await save_file(media)
                if aynav:
                    total_files += 1
                elif vnay == 0:
                    duplicate += 1
                elif vnay == 2:
                    errors += 1
        except Exception as e:
            logger.exception(e)
            await msg.edit(f'Error: {e}')
        else:
            await msg.edit(f'Succesfully saved <code>{total_files}</code> to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>')
