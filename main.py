from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import markdown as md
from MySQLdb import Error
from assistants import Storekeeper
import logging
import MySQLdb as msdb


API_TOKEN = '6238808085:AAGIrojIMTdS-3V96gDjAbMn6NIkULDmGzc'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
sk = None
try:
    db = msdb.connect(
            host='localhost',
            database='tcb_db',
            user='Abdurakhmon',
            password='longwaythroughchallenges2002811@'
        )
    sk = Storekeeper(db)
except Error as e:
    print('An error happened while trying to make a connection to MySql: ', e)
else:
    cursor = db.cursor()
    if sk.table_exists('users') is False:
        user_table = f"chat_id BIGINT, fname VARCHAR(150), lname VARCHAR(150), username VARCHAR(100), CONSTRAINT pk_user PRIMARY KEY (chat_id)"
        cursor.execute(f"CREATE TABLE users ({user_table})")
        db.commit()
    print('Connection made successfully!')


@dp.message_handler(commands=['start'])
async def welcome_user(message: types.Message):
    """
    Welcomes the user when start command is sent.
    """

    part1 = "Assalomu alaykum!👋🏻\n"
    part2 = "Hurmatli foydalanuvchi botdan foydalanishni davom etish uchun ism familiyangizni quyidagicha kiriting⬇️\n\n"
    part3 = md.code("FI:Boltayev Bolta\n\n", sep='')
    part4 = "⚠️Birinchi familiya, so'ng ism yozilishi shart⚠️"
    await message.reply(part1 + part2 + part3 + part4, parse_mode=types.ParseMode.MARKDOWN)


@dp.message_handler()
async def save_users_names(message: types.Message):
    """
    Gets the user's first and last names and saves them to the database.
    """

    if message.text.startswith('FI:'):
        names = message.text.replace('FI:', '').split()
        if not sk.user_exists('users', message.chat['id']):
            if len(names) < 3:
                values = f"'{message.chat['id']}', '{names[1]}', '{names[0]}', '{message.chat['username']}'"
                cursor.execute(
                    f"""INSERT INTO users (chat_id, fname, lname, username) VALUES ({values})"""
                    )
                db.commit()
                await message.reply(f"Tanishganimdan xursandman, {names[1]}!\nEndi botdan foydalanishingiz mumkin🙂")
            else:
                await message.reply("Ism familiyangizni yuqorida ko'rsatilgan formatda kiritmaganga o'xshaysiz🤨")
        else:
            await message.reply("Siz ro'yxatdan o'tgansiz!")


if __name__ == '__main__':
    executor.start_polling(dp)
