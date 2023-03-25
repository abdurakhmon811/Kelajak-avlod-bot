"""
NOTE: When creating tables for users, keep in mind that the table should be called USERS(in lower case).
Otherwise, multiple errors can happen. And the same principle goes for tests and channels.
"""
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import markdown as md
from aiogram.utils.exceptions import BadRequest
from assistants import Channel, \
    DBFactory, \
    Storekeeper, \
    Test, TestResult, \
    User, \
    get_items_in_dict, get_percent, get_test_code, \
    item_has_space, \
    names_valid, \
    separate_by
from MySQLdb import Error
import MySQLdb as msdb
import logging
import re
import time


API_TOKEN = '6238808085:AAGIrojIMTdS-3V96gDjAbMn6NIkULDmGzc'
bot_owner_id = 1170330985
bot_owner_url = 'https://t.me/abduraxmonomonov'
superuser_panel_password = '6238808AAG'
admin_password = 8808085
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
sk = None
user_model = None
fac = None
channel = None
test = None
test_results = None
try:
    db = msdb.connect(
            host='localhost',
            database='tcb_db',
            user='Abdurakhmon',
            password='longwaythroughchallenges2002811@'
        )
    sk = Storekeeper(db)
    user_model = User(db)
    fac = DBFactory(db)
    channel = Channel(db)
    test = Test(db)
    test_results = TestResult(db)
except Error as e:
    print('An error happened while trying to make a connection to MySql: ', e)
else:
    cursor = db.cursor()
    if sk.table_exists('users') is False:
        fac.create_table(
            'users', 
            fac.integerfield('chat_id'), 
            fac.charfield('fname', 150, long_text=True), 
            fac.charfield('lname', 150, long_text=True), 
            fac.charfield('phone_number', 13),
            fac.charfield('address', 200, long_text=True),
            fac.charfield('school', 100, long_text=True),
            fac.charfield('class', 50),
            fac.charfield('username', 100, long_text=True), 
            fac.integerfield('is_superuser', 'tinyint'), 
            fac.integerfield('is_admin', 'tinyint'),
            fac.set_constraint('pk_user', 'chat_id'),
        )
    if sk.table_exists('tests') is False:
        fac.create_table(
            'tests', 
            fac.integerfield('test_id'),
            fac.charfield('test_subject', 150, long_text=True),
            fac.charfield('creator', 150, long_text=True), 
            fac.charfield('answers', 400, long_text=True), 
            fac.datetimefield('date_created'),
            fac.datetimefield('date_deactivated'),
            fac.integerfield('is_active', 'TINYINT', 1), 
            fac.set_constraint('pk_test', 'test_id'),
        )
    if sk.table_exists('test_results') is False:
        fac.create_table(
            'test_results',
            fac.datetimefield('date_taken'),
            fac.charfield('test_taker', 150, long_text=True),
            fac.integerfield('test_id'),
            fac.charfield('test_subject', 150, long_text=True),
            fac.integerfield('questions_length'),
            fac.integerfield('correct_answers'),
            fac.integerfield('incorrect_answers'),
            fac.charfield('user_answers', 300, long_text=True),
        )
    if sk.table_exists('channels') is False:
        fac.create_table(
            'channels',
            fac.charfield('username', 300, long_text=True),
            fac.datetimefield('date_added', date_only=True),
            fac.set_constraint('pk_channel', 'username'),
        )
    print('Database connection made successfully!')

# Keyboard buttons
addChannelBtn = KeyboardButton("Obuna uchun kanal qo'shish ➕") # issues are present
addTestBtn = KeyboardButton("Test qo'shish ➕")
availableTestsBtn = KeyboardButton("Testlar 🗂")
checkTestBtn = KeyboardButton("Test javoblarini tekshirish ✅") # DONE, issues are present
deactivateTestBtn = KeyboardButton("Testni to'xtatish ⛔️") # DONE, issues are present
getAdminBtn = KeyboardButton("Test kiritish huquqini olish ✅")
getTestResultsBtn = KeyboardButton("Test natijalarini ko'rish 📊") # DONE, issues are present
giveSuperuserBtn = KeyboardButton("Oliy admin huquqini berish 👨🏻‍✈️")
myInfoBtn = KeyboardButton("Mening ma'lumotlarim 📄") # DONE, issues are present
usersCountBtn = KeyboardButton("Foydalanuvchilar 👤") # not done
kb = ReplyKeyboardMarkup(resize_keyboard=True).row(getAdminBtn, checkTestBtn).add(myInfoBtn)
superuser_kb = ReplyKeyboardMarkup(resize_keyboard=True)
superuser_kb.add(addChannelBtn).row(addTestBtn, availableTestsBtn).add(deactivateTestBtn).add(checkTestBtn)
superuser_kb.add(getTestResultsBtn)
superuser_kb.add(myInfoBtn, usersCountBtn).add(giveSuperuserBtn)
admin_kb = ReplyKeyboardMarkup(resize_keyboard=True).row(addTestBtn, checkTestBtn).add(getTestResultsBtn).add(myInfoBtn)


class Form(StatesGroup):
    
    add_test = State()
    add_channel = State()
    address = State()
    change_address = State()
    change_class = State()
    change_names = State()
    change_phone_number = State()
    change_school = State()
    class_ = State()
    give_superuser = State()
    names = State()
    phone_number = State()
    school = State()
    stop_test = State()
    superuser_password = State()
    test_check = State()
    test_results = State()


cancallable_states = (
    Form.add_test,
    Form.add_channel,
    Form.change_address,
    Form.change_class,
    Form.change_names,
    Form.change_phone_number,
    Form.change_school,
    Form.give_superuser,
    Form.stop_test,
    Form.superuser_password,
    Form.test_check, 
    Form.test_results,
)


# Handlers for everyone
@dp.message_handler(commands=['cancel'], state=cancallable_states)
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_states(message: types.Message, state: FSMContext):
    """
    Cancels any active states if cancel command is called or cancel keyword is written.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    await message.reply(
        "Bekor qilindi\.\n\n%s" % md.code('Owned by abduraxmonomonov.uz'), 
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )
    await state.finish()


@dp.message_handler(state=Form.change_address)
async def change_address(message: types.Message, state: FSMContext):
    """
    Changes the address of the request user.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if len(message.text) < 100 and message.text[-1] not in '👤📄👨🏻‍✈️📊➕⛔️✅🤨🗂':
        user_model.change_address(
            message.chat['id'], 
            re.sub(r'[^a-zA-Z0-9,]', ' ', message.text)
        )
        await message.reply(
            "Ajoyib\! Manzilingiz o'zgartirildi 🙂\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
    else:
        await message.reply(
            "Iltimos, to'g'ri manzil kiriting\! Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.callback_query_handler(lambda call: str(call.data) == 'change_address')
async def change_address_state(callback_query: types.CallbackQuery):
    """
    Tells the user how to send their address and activates the CHANGE_ADDRESS state.
    """

    await Form.change_address.set()
    await callback_query.message.answer(
        "Manzilingizni kiriting\. Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s" % \
        md.code("Owned by abduraxmonomonov.uz"),
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )


@dp.message_handler(state=Form.change_class)
async def change_class(message: types.Message, state: FSMContext):
    """
    Changes the class of the request user.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if len(message.text) <= 5 and message.text[-1] not in '👤📄👨🏻‍✈️📊➕⛔️✅🤨🗂':
        user_model.change_class(
            message.chat['id'], 
            re.sub(r'[^a-zA-Z0-9]', '', message.text),
        )
        await message.reply(
            "Ajoyib\! Sinfingiz o'zgartirildi 🙂\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
    else:
        await message.reply(
            "Iltimos, yuqorida eslatib o'tilgan qoidalarga rioya qilgan holda sinfni kiriting\! " \
            "Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2, 
        )


@dp.callback_query_handler(lambda call: str(call.data) == 'change_class')
async def change_class_state(callback_query: types.CallbackQuery):
    """
    Tells the user how to send their class and activates the CHANGE_CLASS state.
    """

    await Form.change_class.set()
    await callback_query.message.answer(
        "Sinfingizni kiriting\. Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s\n\n%s" % \
        (
            md.underline("⚠️Harflar va sonlar uzunligi birgalikda 5tadan oshmasligi kerakligini unutmang⚠️"),
            md.code("Owned by abduraxmonomonov.uz"),
        ),
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )


@dp.message_handler(state=Form.change_names)
async def change_names(message: types.Message, state: FSMContext):
    """
    Changes the information (only first and last names) of the request user.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    splitted = message.text.split()
    if len(splitted) == 2 and item_has_space(splitted) is False and names_valid(splitted) is True:
        names = {}
        for name in splitted:
            if name.startswith('I:') or name.startswith('i:'):
                names['first_name'] = name.lower().lstrip('i:').strip()
            elif name.startswith('F:') or name.startswith('f:'):
                names['last_name'] = name.lower().lstrip('f:').strip()
        user_model.change_name(message.chat['id'], names['first_name'].title(), names['last_name'].title())
        await message.reply(
            "Ma'lumotlar o'zgartirildi 🙂\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
    else:
        await message.reply(
            "Familiya va ismingizni yuqorida aytilgandek kiritmaganga o'xshaysiz 🤨\n\n" \
            "Eslatib o'taman familiyangizni oldidan 'f:' ismingizni oldidan esa 'i:' kiritishingiz\n\n" \
            "Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.callback_query_handler(lambda call: str(call.data) == 'change_names')
async def change_names_state(callback_query: types.CallbackQuery):
    """
    Tells the user how to send their names and activates the CHANGE_NAMES state.
    """

    await Form.change_names.set()
    await callback_query.message.answer(
        "Familiyangiz va ismingizni kiriting\. Ismlarda belgi va sonlarga yo'l qo'yilmasligini ham yodda tuting\. " \
        "Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s\n\n%s" % \
        (
            md.underline("⚠️Familiya oldidan 'f:' va ism oldidan 'i:' belgilarini qo'yishni unutmang⚠️"),
            md.code("Owned by abduraxmonomonov.uz"),
        ),
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )


@dp.message_handler(state=Form.change_phone_number)
async def change_phone_number(message: types.Message, state: FSMContext):
    """
    Changes the phone number of the request user.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if message.text.startswith('+998') is True and message.text[1:].isdigit() is True and len(message.text) == 13:
        user_model.change_phone_number(message.chat['id'], message.text)
        await message.reply(
            "Ajoyib\! Telefon raqamingiz o'zgartirildi 🙂\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
    else:
        await message.reply(
            "Telefon raqamingizni yuqorida ko'rsatilgan formatda kiritmaganga o'xshaysiz 🤨\n" \
            "Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.callback_query_handler(lambda call: str(call.data) == 'change_phone_number')
async def change_phone_number_state(callback_query: types.CallbackQuery):
    """
    Tells the user how to send their phone number and activates the CHANGE_PHONE_NUMBER state.
    """

    await Form.change_phone_number.set()
    await callback_query.message.answer(
        "Telefon raqamingizni kiriting\. Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s\n\n%s" % \
        (
            md.underline("⚠️Telefon raqamni +998901234567 formatida kiritishni unutmang⚠️"),
            md.code("Owned by abduraxmonomonov.uz"),
        ),
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )


@dp.message_handler(state=Form.change_school)
async def change_school(message: types.Message, state: FSMContext):
    """
    Changes the school of the request user.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if len(message.text) < 50 and message.text[-1] not in '👤📄👨🏻‍✈️📊➕⛔️✅🤨🗂':
        user_model.change_school(
            message.chat['id'], 
            re.sub(r'[^a-zA-Z0-9,]', ' ', message.text),
        )
        await message.reply(
            "Ajoyib\! Maktabingiz o'zgartirildi 🙂\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
    else:
        await message.reply(
            "Iltimos, yuqorida eslatib o'tilgan qoidalarga rioya qilgan holda maktabni kiriting\! " \
            "Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.callback_query_handler(lambda call: str(call.data) == 'change_school')
async def change_school_state(callback_query: types.CallbackQuery):
    """
    Tells the user how to send their school and activates the CHANGE_SCHOOL state.
    """

    await Form.change_school.set()
    await callback_query.message.answer(
        "Maktabingizni kiriting\. Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s\n\n%s" % \
        (
            md.underline("⚠️Harflar va sonlar uzunligi birgalikda 50tadan oshmasligi kerakligini unutmang⚠️"),
            md.code("Owned by abduraxmonomonov.uz"),
        ),
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )


@dp.callback_query_handler(lambda call: str(call.data).startswith('check_subscription:'))
async def check_subscription(callback_query: types.CallbackQuery):
    """
    Checks if a user has subscribed the channel or not.
    """

    latest_channel = channel.get_channel()
    user_id = callback_query.data.split(':')[-1]

    if latest_channel is not None:
        try:
            result = await bot.get_chat_member(latest_channel['username'], user_id)
        except BadRequest:
            await callback_query.answer("Obuna aniqlanmadi! Qaytadan urinib ko'ring.", show_alert=True)
        else:
            if result['status'] == 'left':
                await callback_query.answer("Obuna aniqlanmadi! Qaytadan urinib ko'ring.", show_alert=True)
            else:
                if user_model.get_user_or_users('chat_id', user_id) is None:
                    await callback_query.answer(
                        "Obuna bo'lganingiz uchun rahmat!\n" \
                        "Endi ma'lumotlaringizni kiritib botdan foydalanishingiz mumkin 🙂",
                        show_alert=True,
                    )
                    await no_names(callback_query.message)
                else:
                    await callback_query.answer(
                        "Obuna bo'lganingiz uchun rahmat!\n" \
                        "Endi botdan foydalanishingiz mumkin 🙂",
                        show_alert=True,
                    )


@dp.message_handler(state=Form.test_check)
async def check_test(message: types.Message, state: FSMContext):
    """
    Checks the given test and returns the results of it.
    """

    current_state = await state.get_state()
    if current_state is None:
        return None

    splitted_message = message.text.split(':')
    if (
            len(splitted_message) == 3 and 
            splitted_message[1] != '' and
            item_has_space(splitted_message) is False and not 
            re.findall(r'[^a-zA-Z]', str(splitted_message[2]).lower())
    ):
        test_id = int(splitted_message[0])
        test_subject = str(splitted_message[1]).lower()
        answers = str(splitted_message[2]).lower()
        check_answers = separate_by(answers, ',').split(',')
        test_ = test.get_test(test_id)
        if test_ is None:
            await message.reply(
                "%s raqamli test topilmadi\!\n\n%s" % (test_id, md.code('Owned by abduraxmonomonov.uz')),
                parse_mode=types.ParseMode.MARKDOWN_V2,
            )
        else:
            if test_subject == str(test_['test_subject']).lower():
                if len(check_answers) == len(str(test_['answers']).split(',')):
                    if test_['is_active'] is True:
                        correct_answers = get_items_in_dict(str(test_['answers']).split(','))
                        answers = get_items_in_dict(separate_by(answers, ',').split(','))
                        await check_results(message, test_id, answers, correct_answers)
                        await state.finish()
                    else:
                        await message.reply(
                            "%s raqamli test to'xtatilgan\!\n\n%s" % \
                            (test_id, md.code('Owned by abduraxmonomonov.uz')),
                            parse_mode=types.ParseMode.MARKDOWN_V2,
                        )
                else:
                    await message.reply(
                        "%s raqamli test savollari soni bilan sizning javoblaringizni soni bir xil emas 🤨\n\n%s" % \
                        (test_id, md.code('Owned by abduraxmonomonov.uz')),
                        parse_mode=types.ParseMode.MARKDOWN_V2,
                    )
            else:
                await message.reply(
                    "%s raqamli test mavjud, biroq fan nomi noto'g'ri 🤨\n\n%s" % \
                    (test_id, md.code('Owned by abduraxmonomonov.uz')),
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
    else:
        await message.reply(
            "Test javoblarini yuqorida ko'rsatilgan formatda kiritmaganga o'xshaysiz 🤨\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.callback_query_handler(lambda call: str(call.data).startswith('deny_admin_to:'))
async def deny_admin(callback_query: types.CallbackQuery):
    """
    Denies to give admin priviliges to the user with the corresponding id.
    """

    chat_id = str(callback_query.data).split(':')[-1]
    user = user_model.get_user_or_users('chat_id', chat_id)
    await bot.send_message(
        chat_id,
        "Afsuski, test kiritish huquqi uchun so'rovingiz rad etildi ⛔️\n\n%s" % \
        md.code('Owned by abduraxmonomonov.uz'),
        parse_mode=types.ParseMode.MARKDOWN_V2,
        reply_markup=kb,
    )
    await callback_query.message.answer(
        f"{user['first_name']} {user['last_name']}'ga test kiritish huquqini berish rad etildi ⛔️\n\n" \
        f"{md.code('Owned by abduraxmonomonov.uz')}",
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )


@dp.message_handler(Text(equals="Test kiritish huquqini olish ✅"))
async def get_admin(message: types.Message):
    """
    Sends superusers to give admin priviliges to the request user.
    """

    superusers = user_model.get_user_or_users('is_superuser', 1, many=True)
    latest_channel = channel.get_channel()
    user = user_model.get_user_or_users('chat_id', message.chat['id'])
    
    if user is None:
        if latest_channel is None:
            await no_names(message)
        else:
            try:
                result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
            except BadRequest:
                await no_subscription(message)
            else:
                if result['status'] == 'left':
                    await no_subscription(message)
                else:
                    await no_names(message)
    else:
        if latest_channel is None:
            if user['is_superuser'] is False and user['is_admin'] is False:
                giveAdminBtns = InlineKeyboardMarkup()
                giveAdminBtns.add(
                    InlineKeyboardButton("Taqdim etish ✅", callback_data=f"give_admin_to:{user['chat_id']}")
                )
                giveAdminBtns.add(
                    InlineKeyboardButton("Rad etish ⛔️", callback_data=f"deny_admin_to:{user['chat_id']}")
                )
                for suser in superusers:
                    await bot.send_message(
                        suser['chat_id'],
                        f"{user['first_name']} {user['last_name']} test kiritish huquqini so'ramoqda\.\n\n" \
                        f"{md.code('Owned by abduraxmonomonov.uz')}",
                        parse_mode=types.ParseMode.MARKDOWN_V2,
                        reply_markup=giveAdminBtns,
                    )
                await message.reply(
                    "So'rov jo'natildi ✅\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
            else:
                await message.reply(
                    "Sizda allaqachon test kiritish huquqi mavjud\!\n\n%s" % \
                    md.code('Owned by abduraxmonomonov.uz'),
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
        else:
            try:
                result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
            except BadRequest:
                await no_subscription(message)
            else:
                if result['status'] == 'left':
                    await no_subscription(message)
                else:
                    if user['is_superuser'] is False and user['is_admin'] is False:
                        giveAdminBtns = InlineKeyboardMarkup()
                        giveAdminBtns.add(
                            InlineKeyboardButton("Taqdim etish ✅", callback_data=f"give_admin_to:{user['chat_id']}")
                        )
                        giveAdminBtns.add(
                            InlineKeyboardButton("Rad etish ⛔️", callback_data=f"deny_admin_to:{user['chat_id']}")
                        )
                        for superuser in superusers:
                            await bot.send_message(
                                superuser['chat_id'],
                                f"{user['first_name']} {user['last_name']} test kiritish huquqini so'ramoqda\.\n\n" \
                                f"{md.code('Owned by abduraxmonomonov.uz')}",
                                parse_mode=types.ParseMode.MARKDOWN_V2,
                                reply_markup=giveAdminBtns,
                            )
                        await message.reply(
                            "So'rov jo'natildi ✅\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
                            parse_mode=types.ParseMode.MARKDOWN_V2,
                        )
                    else:
                        await message.reply(
                            "Sizda allaqachon test kiritish huquqi mavjud\!\n\n%s" % \
                            md.code('Owned by abduraxmonomonov.uz'),
                            parse_mode=types.ParseMode.MARKDOWN_V2,
                        )


@dp.callback_query_handler(lambda call: str(call.data).startswith('give_admin_to:'))
async def give_admin(callback_query: types.CallbackQuery):
    """
    Gives admin priviliges to the user with the corresponding id.
    """

    chat_id = str(callback_query.data).split(':')[-1]
    user = user_model.get_user_or_users('chat_id', chat_id)
    try:
        user_model.promote_to_admin(chat_id)
    except AttributeError:
        await callback_query.answer(
            f"{user['first_name']} {user['last_name']}ga allaqachon 'admin' unvoni berilgan!", show_alert=True,
        )
    else:
        await bot.send_message(
            chat_id,
            "Test kiritish huquqi uchun so'rovingiz qabul qilindi ✅ Endi test kirita olishingiz mumkin 🙂\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
            reply_markup=admin_kb,
        )
        await callback_query.message.answer(
            f"{user['first_name']} {user['last_name']}'ga test kiritish huquqi taqdim etildi ✅\n\n" \
            f"{md.code('Owned by abduraxmonomonov.uz')}",
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.message_handler(commands=['help'], state='*')
async def help(message: types.Message, state: FSMContext):
    """
    Shows the manual on how to use the bot.
    """

    current_state = await state.get_state()
    if current_state is None:
        help_text = "/start \- buyrug'i botdan foydalanishni boshlash uchun kiritiladi\. " \
        "Bosilgandan so'ng, agar kanalga obuna bo'lgan bo'lsangiz, bir qancha ma'lumotlarni " \
        "kiritishingiz so'raladi\(bu xizmat sifatini yaxshilash uchun muhim\)\. Agar kanaldan " \
        "obunangiz topilmasa, obuna bo'lish so'raladi\(asosiy ma'lumotlar ayni o'sha kanalda chiqariladi\)\." \
        "So'ng esa ma'lumotlaringizni kiritib botdan foydalanishingiz mumkin bo'ladi\.\n\n" \
        "/menu \- buyrug'i asosiy menyuni ochish uchun ishlatiladi\. Asosiy menyuda siz test "\
        "kiritish huquqi uchun da'vogarlik qilishingiz, testingizni javoblarini tekshirishingiz " \
        "va ma'lumotlaringizni ko'rishingiz mumkin bo'ladi\.\n\n" \
        "/my\_info \- buyrug'i ma'lumotlaringizni ko'rish uchun ishlatiladi\.\n\n" \
        "/cancel \- buyrug'i holatlarni bekor qilish uchun ishlatiladi\. Holatlar \- " \
        "ma'lum bir buyruq kiritilgandan yoki tugma bosilgandan so'ng ochiladi\.\n\n" \
        "Shuningdek, aksariyat xabarlarni ostgi qismida qoidalar/tushuntirishlar kiritilgan, ularga " \
        "rioya qilmasangiz kutgan natijalaringizni ola olmaysiz\.\n\n%s" % md.code('Owned by abduraxmonomonov.uz')
        await message.reply(help_text, parse_mode=types.ParseMode.MARKDOWN_V2)


@dp.message_handler(commands=['my_info'], state='*')
@dp.message_handler(Text(equals="Mening ma'lumotlarim 📄"), state='*')
async def my_info(message: types.Message, state: FSMContext):
    """
    Shows information about a user.
    """

    current_state = await state.get_state()
    if current_state is None:
        latest_channel = channel.get_channel()
        user = user_model.get_user_or_users('chat_id', message.chat['id'])
        if user is None:
            if latest_channel is None:
                await no_names(message)
            else:
                try:
                    result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
                except BadRequest:
                    await no_subscription(message)
                else:
                    if result['status'] == 'left':
                        await no_subscription(message)
                    else:
                        await no_names(message)
        else:
            if user['is_superuser'] is True and user['is_admin'] is True:
                await send_user_info(message, user)
            else:
                if latest_channel is None:
                    await send_user_info(message, user)
                else:
                    try:
                        result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
                    except BadRequest:
                        await no_subscription(message)
                    else:
                        if result['status'] == 'left':
                            await no_subscription(message)
                        else:
                            await send_user_info(message, user)


@dp.message_handler(commands=['menu'], state='*')
@dp.message_handler(Text(equals='asosiy menyu', ignore_case=True), state='*')
async def open_menu(message: types.Message, state: FSMContext):
    """
    Opens the main menu.
    """

    current_state = await state.get_state()
    if current_state is None:
        latest_channel = channel.get_channel()
        user = user_model.get_user_or_users('chat_id', message.chat['id'])
        if user is None:
            if latest_channel is None:
                await no_names(message)
            else:
                try:
                    result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
                except BadRequest:
                    await no_subscription(message)
                else:
                    if result['status'] == 'left':
                        await no_subscription(message)
                    else:
                        await no_names(message)
        else:
            if latest_channel is None:
                await show_appropriate_panel(message, user['is_superuser'], user['is_admin'])
            else:
                try:
                    result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
                except BadRequest:
                    await no_subscription(message)
                else:
                    if result['status'] == 'left':
                        await no_subscription(message)
                    else:
                        await show_appropriate_panel(message, user['is_superuser'], user['is_admin'])


@dp.message_handler(state=Form.address)
async def register_address(message: types.Message, state: FSMContext):
    """
    Gets the user's address and saves it to the database.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if (
            len(message.text) < 100 and len(message.text) > 10 and
            message.text[-1] not in '👤📄👨🏻‍✈️📊➕⛔️✅🤨🗂' and 
            message.text != '/cancel'
    ):
        user_model.change_address(
            message.chat['id'], 
            re.sub(r'[^a-zA-Z0-9,]', ' ', message.text)
        )
        await message.reply(
            "Juda soz, endi ayni damda o'zingiz ta'lim olayotgan maktabni yoki farzandingiz ta'lim " \
            "olayotgan maktabni kiriting\. Harflar va sonlarni birgalikdagi uzunligi 50tadan oshib ketmasligini ham " \
            f"ta'minlang\!\n\n Misol \-\> {md.code('Qarshi shahri, 15-maktab')}\n\n " \
            f"{md.code('Owned by abduraxmonomonov.uz')}",
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
        await Form.school.set()
    else:
        await message.reply(
            "Iltimos, to'g'ri manzil kiriting\!\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.message_handler(state=Form.class_)
async def register_class(message: types.Message, state: FSMContext):
    """
    Gets the class where the user or their children study and saves it to the database.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if len(message.text) <= 5 and len(message.text) >= 2 and message.text[-1] not in '👤📄👨🏻‍✈️📊➕⛔️✅🤨🗂':
        user_model.change_class(message.chat['id'], re.sub(r'[^a-zA-Z0-9,]', ' ', message.text.upper()))
        await message.reply(
            "Ajoyib\-u g'aroyib\! Ma'lumotlaringiz saqlandi endi botdan foydalanishingiz mumkin 🙂\n\n" \
            "Eslatma: Yuqorida olingan barcha ma'lumotlar xizmat sifatini yaxshilash uchun xizmat qiladi va ma'sul " \
            "shaxslardan boshqa hech kimning qo'liga tushmasligi kafolatlanadi\!\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
    else:
        await message.reply(
            "Iltimos, yuqorida eslatib o'tilgan qoidalarga rioya qilgan holda sinfni kiriting\!\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2, 
        )


@dp.message_handler(state=Form.phone_number)
async def register_phone_number(message: types.Message, state: FSMContext):
    """
    Gets the user's phone number and saves it to the database.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if message.text.startswith('+998') is True and message.text[1:].isdigit() is True and len(message.text) == 13:
        user_model.change_phone_number(message.chat['id'], message.text)
        await message.reply(
            "Ajoyib\! Telefon raqamingiz ham saqlandi\. Navbat manzilingizga, manzilingizni kiriting\.\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
        await Form.address.set()
    else:
        await message.reply(
            "Telefon raqamingizni yuqorida ko'rsatilgan formatda kiritmaganga o'xshaysiz 🤨\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.message_handler(state=Form.school)
async def register_school(message: types.Message, state: FSMContext):
    """
    Gets the school where the user or their children study and saves it to the database.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if len(message.text) < 50 and message.text[-1] not in '👤📄👨🏻‍✈️📊➕⛔️✅🤨🗂':
        user_model.change_school(message.chat['id'], re.sub(r'[^a-zA-Z0-9,]', ' ', message.text))
        await message.reply(
            "Maktabingiz saqlandi 🙂, va nihoyat so'nggi qadam, maktabdagi sinfingizni yoki farzandingizni sinfini " \
            "kiriting\. Shuningdek, harflar va sonlarning birgalikdagi uzunligi 5tadan oshib ketmasligi kerak " \
            "ekanligini ham yodda tuting\!\n\n Misol \-\> %s\n\n%s" % \
            (md.code('3V'), md.code('Owned by abduraxmonomonov.uz')),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
        await state.finish()
        await Form.class_.set()
    else:
        await message.reply(
            "Iltimos, yuqorida eslatib o'tilgan qoidalarga rioya qilgan holda maktabni kiriting\!\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.message_handler(state=Form.names)
async def register_names(message: types.Message, state: FSMContext):
    """
    Gets the user's first and last names and saves them to the database.
    """

    current_state = await state.get_state()
    if current_state is None:
        return

    splitted = message.text.split()
    if len(splitted) == 2 and item_has_space(splitted) is False and names_valid(splitted) is True:
        names = {}
        for name in splitted:
            if name.startswith('I:') or name.startswith('i:'):
                names['first_name'] = name.lower().lstrip('i:').strip()
            elif name.startswith('F:') or name.startswith('f:'):
                names['last_name'] = name.lower().lstrip('f:').strip()
        columns = ['chat_id', 'fname', 'lname', 'username', 'is_superuser', 'is_admin']
        values = [
            message.chat['id'], 
            names['first_name'].title(), 
            names['last_name'].title(), 
            message.chat['username'], 
            1 if message.chat['id'] == bot_owner_id else 0,
            1 if message.chat['id'] == bot_owner_id else 0,
        ]
        sk.get_supplies('users', columns, values)
        await message.reply(
            f"Tanishganimdan xursandman, {names['first_name'].title()}\!\n\n" \
            f"Endi telefon raqamingizni \+998901234567 formatida kiriting \n\n " \
            f"{md.code('Owned by abduraxmonomonov.uz')}",
            parse_mode=types.ParseMode.MARKDOWN_V2,
            reply_markup=kb,
        )
        await state.finish()
        await Form.phone_number.set()
    else:
        await message.reply(
            "Ism familiyangizni yuqoridagi misolda ko'rsatilgan formatda kiritmaganga o'xshaysiz 🤨\. " \
            "Ismlarda belgi va sonlarga yo'l qo'yilmasligini ham yodda tuting\.\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.message_handler(Text(equals="Test javoblarini tekshirish ✅"))
async def set_test_checking_state(message: types.Message):
    """
    Sets the test checking state and tells the user how to send the answers.
    """

    latest_channel = channel.get_channel()
    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user is None:
        if latest_channel is None:
            await no_names(message)
        else:
            try:
                result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
            except BadRequest:
                await no_subscription(message)
            else:
                if result['status'] == 'left':
                    await no_subscription(message)
                else:
                    await no_names(message)
    else:
        if latest_channel is None:
            await get_test_answers(message)
        else:
            try:
                result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
            except BadRequest:
                await no_subscription(message)
            else:
                if result['status'] == 'left':
                    await no_subscription(message)
                else:
                    await get_test_answers(message)


@dp.message_handler(commands=['start'], state='*')
async def welcome_user(message: types.Message, state: FSMContext):
    """
    Welcomes the user when start command is sent.
    """

    current_state = await state.get_state()
    if current_state is None:
        latest_channel = channel.get_channel()
        user = user_model.get_user_or_users('chat_id', message.chat['id'])
        if user is None:
            if latest_channel is None:
                await no_names(message)
            else:
                try:
                    result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
                except BadRequest:
                    await no_subscription(message)
                else:
                    if result['status'] == 'left':
                        await no_subscription(message)
                    else:
                        await no_names(message)
        else:
            is_superuser = user['is_superuser']
            is_admin = user['is_admin']
            if latest_channel is None:
                text = "Assalomu alaykum, %s\! 👋🏻\n\n" % user['first_name']
                text2 = "Sizni qayta ko'rib turganimdan xursandman 🙂\n\n%s" % md.code("Owned by abduraxmonomonov.uz")
                await message.reply(text + text2, parse_mode=types.ParseMode.MARKDOWN_V2)
                await show_appropriate_panel(message, is_superuser, is_admin)
            else:
                try:
                    result = await bot.get_chat_member(latest_channel['username'], message.chat['id'])
                except BadRequest:
                    text = "Assalomu alaykum, %s\! 👋🏻\n\n" % user['first_name']
                    text2 = "Sizni qayta ko'rib turganimdan xursandman 🙂 " \
                    "Biroq, Kanalimizdan chiqib ketganga o'xshaysiz 🤨" \
                    "Botdan foydalanishni davom etish uchun qayta obuna bo'ling\.\n\n%s" % \
                    md.code("Owned by abduraxmonomonov.uz")
                    subscribe_url = 'https://t.me/' + str(latest_channel['username']).lstrip('@')
                    subscribeBtns = InlineKeyboardMarkup()
                    subscribeBtns.add(InlineKeyboardButton("Obuna bo'lish", subscribe_url))
                    subscribeBtns.add(
                        InlineKeyboardButton("Obuna bo'ldim ✅", callback_data=f"check_subscription:{message.chat['id']}")
                    )
                    await message.reply(text + text2, parse_mode=types.ParseMode.MARKDOWN_V2, reply_markup=subscribeBtns)
                else:
                    if result['status'] == 'left':
                        text = "Assalomu alaykum, %s\! 👋🏻\n\n" % user['first_name']
                        text2 = "Sizni qayta ko'rib turganimdan xursandman 🙂 " \
                        "Biroq, Kanalimizdan chiqib ketganga o'xshaysiz 🤨" \
                        "Botdan foydalanishni davom etish uchun qayta obuna bo'ling\.\n\n%s" % \
                        md.code("Owned by abduraxmonomonov.uz")
                        subscribe_url = 'https://t.me/' + str(latest_channel['username']).lstrip('@')
                        subscribeBtns = InlineKeyboardMarkup()
                        subscribeBtns.add(InlineKeyboardButton("Obuna bo'lish", subscribe_url))
                        subscribeBtns.add(
                            InlineKeyboardButton(
                                "Obuna bo'ldim ✅", 
                                callback_data=f"check_subscription:{message.chat['id']}"
                            )
                        )
                        await message.reply(
                            text + text2, 
                            parse_mode=types.ParseMode.MARKDOWN_V2, 
                            reply_markup=subscribeBtns
                        )
                    else:
                        text = "Assalomu alaykum, %s\! 👋🏻\n\n" % user['first_name']
                        text2 = "Sizni qayta ko'rib turganimdan xursandman 🙂\n\n%s" % \
                        md.code("Owned by abduraxmonomonov.uz")
                        await message.reply(text + text2, parse_mode=types.ParseMode.MARKDOWN_V2)
                        await show_appropriate_panel(message, is_superuser, is_admin)


# For the bot owner only
@dp.message_handler(state=Form.give_superuser)
async def give_superuser(message: types.Message, state: FSMContext):
    """
    Promotes the user with the given names to a superuser.
    """

    current_state = await state.get_state()
    if current_state is None:
        return

    splitted = message.text.split()
    if len(splitted) == 2 and item_has_space(splitted) is False and names_valid(splitted) is True:
        names = {}
        for name in splitted:
            if name.startswith('I:') or name.startswith('i:'):
                names['first_name'] = name.lower().lstrip('i:').strip()
            elif name.startswith('F:') or name.startswith('f:'):
                names['last_name'] = name.lower().lstrip('f:').strip()
        first_name = names['first_name'].title()
        last_name = names['last_name'].title()
        user = user_model.get_user_by_name(first_name, last_name)
        if user is None:
            await message.reply(
                f"{first_name} {last_name} ismli foydalanuvchi bazada mavjud emas!"
            )
        else:
            try:
                user_model.promote_to_superuser(user['chat_id'])
            except AttributeError:
                await message.reply(
                    f"{user['first_name']} {user['last_name']}ga allaqachon oliy admin unvoni berilgan!",
                )
            else:
                await bot.send_message(
                    user['chat_id'],
                    "Tabriklayman\! Siz oliy admin darajasigacha oshirildingiz 🙂\n\n%s" % \
                    md.code('Owned by abduraxmonomonov.uz'),
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                    reply_markup=superuser_kb,
                )
                await message.reply(
                    f"{first_name} {last_name} ismli foydalanuvchi oliy admin darajasiga oshirildi."
                )
                await state.finish()
    else:
        await message.reply(
            "Familiya va ismni noto'g'ri kiritdingiz 🤨\n\n" \
            "Ismlarda belgi va sonlarga yo'l qo'yilmasligini ham yodda tuting."
        )


@dp.message_handler(Text(equals="Oliy admin huquqini berish 👨🏻‍✈️"))
async def give_superuser_state(message: types.Message):
    """
    Gives superuser priviliges to a user
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user['is_superuser'] is True and user['is_admin'] is True and user['chat_id'] == bot_owner_id:
        await Form.give_superuser.set()
        await message.reply(
            "Foydalanuvchi familiyasi va ismini kiriting.\n\n " \
            "⚠️Familiya oldidan 'f:' va ism oldidan 'i:' belgilarini qo'yishni unutmang⚠️"
        )
    else:
        await message.reply(
            "Ushbu funksiyadan foydalanish uchun sizda yetarlicha huquqlar mavjud emas\!\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


# For superuser panel
@dp.message_handler(Text(equals="Obuna uchun kanal qo'shish ➕"))
async def add_channel(message: types.Message):
    """
    Gets the request to add a channel to the database.
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user is not None and (user['is_superuser'] is True or user['chat_id'] == bot_owner_id):
        await Form.add_channel.set()
        await message.reply(
            "Kanal uchun foydalanuvchi nomini kiriting\.\n\n Misol \-\> %s\n\n%s" % \
            (md.code("@mening_kanalim"), md.code('Owned by abduraxmonomonov.uz')),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
    else:
        await unknown_command(message)


@dp.message_handler(state=Form.add_channel)
async def check_channel_name(message: types.Message, state: FSMContext):
    """
    Checks if the channel name was inserted correctly. 
    If so, saves the channel into the database, else warns the user.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    channels = channel.get_channel_usernames()
    format = message.text.split()
    if channels:
        if message.text not in channels:
            if message.text.startswith('@') and len(format) == 1 and not re.findall(r'[^a-zA-Z0-9@_]', message.text):
                columns = [
                    'username',
                    'date_added',
                ]
                values = [
                    message.text,
                    time.strftime(r"%Y-%m-%d", time.localtime()),
                ]
                sk.get_supplies('channels', columns, values)
                await message.reply(
                    "Kanal qo'shildi 👍🏻\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
                await state.finish()
            else:
                await message.reply(
                    "Foydalanuvchi nomini yuqorida ko'rsatilgan formatda kiritmaganga o'xshaysiz 🤨\n\n%s" % \
                    md.code('Owned by abduraxmonomonov.uz'),
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
        else:
            await message.reply(
                "Kiritilgan kanal bazada mavjud\!\n\n Bekor qilish uchun /cancel buyrug'ini kiriting\.\n\n%s" % \
                md.code('Owned by abduraxmonomonov.uz'),
                parse_mode=types.ParseMode.MARKDOWN_V2,
            )
    else:
        if message.text.startswith('@') and len(format) == 1 and not re.findall(r'[^a-zA-Z0-9@_]', message.text):
            columns = [
                'username',
                'date_added',
            ]
            values = [
                message.text,
                time.strftime(r"%Y-%m-%d", time.localtime()),
            ]
            sk.get_supplies('channels', columns, values)
            await message.reply("Kanal qo'shildi 👍🏻\n\n%s" % md.code('Owned by abduraxmonomonov.uz'))
            await state.finish()
        else:
            await message.reply(
                "Foydalanuchi nomini yuqorida ko'rsatilgan formatda kiritmaganga o'xshaysiz 🤨\n\n%s" % \
                md.code('Owned by abduraxmonomonov.uz'),
                parse_mode=types.ParseMode.MARKDOWN_V2,
            )


@dp.message_handler(state=Form.superuser_password)
async def check_superuser_password(message: types.Message, state: FSMContext):
    """
    Checks if the superuser password is correct or not.
    """

    current_state = await state.get_state()
    if current_state is None:
        return

    if message.text == superuser_panel_password:
        await message.reply(
            "Oliy admin paneliga xush kelibsiz\! 🙂\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
            reply_markup=superuser_kb,
        )
        await state.finish()
    else:
        await message.reply(
            "Parol noto'g'ri\! \n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.message_handler(Text(equals="Foydalanuvchilar 👤"))
async def get_users(message: types.Message):
    """
    Tells how many users are using the bot.
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user is not None and (user['is_superuser'] is True or user['chat_id'] == bot_owner_id):
        users = user_model.get_user_or_users(all=True)
        out_msg = ''
        for usr in users:
            class_ = str(usr['class']).replace('-', '\-')
            username = '@' + usr['username'] if usr['username'] != "Mavjud emas" else md.underline(usr['username'])
            out_msg += f"{users.index(usr) + 1}\. {usr['first_name']} {usr['last_name']}\n" \
            f"📞Telefon raqam: \{usr['phone_number']}\n📍Manzil: {usr['address']}\n🏫Maktab: {usr['school']}\n" \
            f"🚪Sinf: {class_}\n🔗Foydalanuvchi nomi: {username}\n\n"
        await message.reply(
            "%s holatiga ko'ra, botdan %dta foydalanuvchi foydalanmoqda\.\n\n %s%s" % \
            (
                time.strftime(r"%Y/%m/%d %H:%M:%S", time.localtime()),
                len(users),
                out_msg,
                md.code('Owned by abduraxmonomonov.uz'),
            ),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
    else:
        await unknown_command(message)


@dp.message_handler(Text(equals='oliy-admin-paneliga-kirish'))
async def open_superuser_panel(message: types.Message):
    """
    Opens the superuser panel, requiring the fixed password.
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user is not None and (user['is_superuser'] is True or message.chat['id'] == bot_owner_id):
        await Form.superuser_password.set()
        await message.reply(
            "Parolni kiriting\.\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
    else:
        await unknown_command(message)


@dp.message_handler(Text(equals="Testlar 🗂"))
async def show_tests(message: types.Message):
    """
    Show all the available tests in the database.
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user is not None and (user['is_superuser'] is True or message.chat['id'] == bot_owner_id):
        tests = test.get_tests()
        if tests:
            out_msg = f"""{time.strftime(r"%Y/%m/%d %H:%M:%S", time.localtime())} holatiga ko'ra """ \
            f'{len(tests)}ta test mavjud\.\n\n'
            for test_ in tests:
                answers = \
                '  '.join(
                    [f'{index + 1}\.{str(value).upper()}' for index, value in enumerate(str(test_['answers']).split(','))]
                )
                date_ended = str(test_['date_deactivated']).replace('-', '/')
                date_deactivated = "to'xtatilmagan" if test_['is_active'] is True else date_ended
                test_info = f"🔢 Test raqami: {md.bold(test_['test_id'])}\n" \
                f"📔 Test fani: {str(test_['test_subject']).title().replace('_', ' ')}\n" \
                f"👨🏻‍🏫 Tuzuvchi: {test_['creator']}\n" \
                f"✅ Javoblar: {answers}\n" \
                f"📅 Tuzilgan sana: {str(test_['date_created']).replace('-', '/')}\n" \
                f"⛔️ To'xtatilgan sana: {date_deactivated}\n\n"
                out_msg += test_info
            await message.reply(
                out_msg + md.code('Owned by abduraxmonomonov.uz'), 
                parse_mode=types.ParseMode.MARKDOWN_V2,
            )
        else:
            await message.reply(
                f"""{time.strftime(r"%Y/%m/%d %H:%M:%S", time.localtime())} holatiga ko'ra 0ta testlar mavjud\.\n\n""" \
                f"Testlar hali kiritilmagan 😕\n\n{md.code('Owned by abduraxmonomonov.uz')}",
                parse_mode=types.ParseMode.MARKDOWN_V2,
            )
    else:
        await unknown_command(message)


# For both superuser and admin panels
@dp.message_handler(state=Form.add_test)
async def add_test(message: types.Message, state: FSMContext):
    """
    Adds a test to the database.
    """

    current_state = await state.get_state()
    if current_state is None:
        return

    user = user_model.get_user_or_users('chat_id', message.chat['id'])
    text = message.text.split(':')
    if len(text) == 2 and item_has_space(text) is False and not re.findall(r'[^a-zA-Z]', text[1]):
        ids = test.get_all_test_ids()
        test_id = get_test_code(5, ids)
        test_subject = str(text[0]).lower()
        creator = user['first_name'] + ' ' + user['last_name']
        answers = separate_by(str(text[-1]).lower(), ',')
        questions_number = len(answers.split(','))
        date_created = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime())
        sk.get_supplies(
            'tests',
            [
                'test_id',
                'test_subject',
                'creator',
                'answers',
                'date_created',
            ],
            [
                test_id,
                test_subject,
                creator,
                answers,
                date_created,
            ],
        )
        stopTestBtns = InlineKeyboardMarkup()
        await message.reply(
            f"Test raqami: {test_id}\n" \
            f"Test fani: {test_subject.title().replace('_', ' ')}\n" \
            f"Tuzuvchi: {creator}\n" \
            f"Savollar soni: {questions_number}\n" \
            f"Tuzilgan sana: {date_created.replace('-', '/')}\n" \
            f"Holati: faol\n\n" \
            "Test bazaga qo'shildi 👌🏻 \n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
            reply_markup=stopTestBtns.add(
                InlineKeyboardButton("Testni to'xtatish ⛔️", callback_data=f"stop_test:{test_id}")
            )
        )
        await state.finish()
    else:
        await message.reply(
            "Testni yuqorida ko'rsatilgan formatda kiritmaganga o'xshaysiz 🤨\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.callback_query_handler(lambda callback: str(callback.data).startswith('stop_test:'))
async def cancel_test(callback_query: types.CallbackQuery):
    """
    Retrieves the test with the given id and sets its is_active property to 0(False).
    """

    test_id = str(callback_query.data).split(':')[-1]
    test_ = test.get_test(test_id)

    if test_ and test_['is_active'] is True:
        try:
            test.deactivate(test_id)
        except ValueError:
            await callback_query.answer("%s raqamli test mavjud emas!" % test_id, show_alert=True)
        except AttributeError:
            await callback_query.answer("%s raqamli test allaqachon to'xtatilgan!" % test_id, show_alert=True)
        else:
            dicted_answers = get_items_in_dict(str(test_['answers']).split(','))
            results = test_results.get_results(test_['test_id'])
            if results:
                await send_test_results(callback_query.message, test_, results, dicted_answers)
            await callback_query.message.answer(
                "Test to'xtatildi\! Natijalarni menyu orqali ko'rishingiz mumkin 🙂\n\n%s" % \
                md.code('Owned by abduraxmonomonov.uz'),
                parse_mode=types.ParseMode.MARKDOWN_V2,
            )


@dp.message_handler(Text(equals="Test qo'shish ➕"))
async def get_new_test(message: types.Message):
    """
    Tells a user how to send the answers
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user is not None:
        if user['is_superuser'] == True or user['is_admin'] == True or user['chat_id'] == bot_owner_id:
            await Form.add_test.set()
            await message.reply(
                "Test raqami avtomatik tarzda chiqariladi, " \
                "siz faqat test javoblarini quyidagi ko'rinishda kiriting ⬇️\n\n"  \
                "<fan\_nomi\>:ABCDABCDABCDABCD\.\.\.\n\n%s\n\n%s" % \
                (
                    "Shuningdek, fan nomini kiritguncha so'zlar orasida joy tashlash o'rniga \_ belgisini qo'yish " \
                    "yodingizdan ko'tarilmasin\!",
                    md.code('Owned by abduraxmonomonov.uz')
                ),
                parse_mode=types.ParseMode.MARKDOWN_V2,
            )
    else:
        await unknown_command(message)


@dp.message_handler(Text(equals="Test natijalarini ko'rish 📊"))
async def get_test_id(message: types.Message):
    """
    Returns the test results by the test creator.
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user is not None and (user['is_admin'] is True or user['is_superuser'] is True):
        await Form.test_results.set()
        await message.reply(
            "Test raqamini kiriting\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
    else:
        await unknown_command(message)


@dp.message_handler(state=Form.test_results)
async def get_test_results(message: types.Message, state: FSMContext):
    """
    Shows the user their test results or tells that the test with the given id does not exist in case the test not found.
    """

    current_state = await state.get_state()
    if current_state is None:
        return
    
    if len(message.text) == 5:
        test_ = test.get_test(message.text)
        if test_ is not None:
            results = test_results.get_results(test_['test_id'])
            is_active = "to'xtatilmagan" if test_['is_active'] is True else str(test_['end_date']).replace('-', '/')
            if results:
                out_msg = f"Test raqami: {test_['test_id']}\n" \
                f"Test fani: {str(test_['test_subject']).title().replace('_', ' ')}\n" \
                f"Tuzuvchi: {test_['creator']}\n" \
                f"Savollar soni: {len(str(test_['answers']).split(','))}\n" \
                f"Tuzilgan sana: {str(test_['start_date']).replace('-', '/')}\n" \
                f"To'xtatilgan sana: {is_active}\n\n" \
                f"{time.strftime(r'%Y/%m/%d %H:%M:%S', time.localtime())} holati bo'yicha natijalar:\n\n"
                # Value here is a dict
                for index, value in enumerate(results):
                    out_msg += f"{index + 1}\. {value['test_taker']} \- {value['correct_answers']} ✅"
                out_msg = out_msg + '\n\n' + md.code('Owned by abduraxmonomonov.uz')
                await message.reply(
                    out_msg,
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
                await state.finish()
            else:
                await message.reply(
                    f"{test_['test_id']} raqamli test bo'yicha natijalar hali mavjud emas\.\.\.\n\n" \
                    f"{md.code('Owned by abduraxmonomonov.uz')}",
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
                await state.finish()
        else:
            await message.reply(
                f'{message.text} raqamli test mavjud emas\!\n\n{md.code("Owned by abduraxmonomonov.uz")}',
                parse_mode=types.ParseMode.MARKDOWN_V2,
            )
    else:
        await message.reply(
            "Test raqami 5ta sondan iborat 🤨\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.message_handler(state=Form.stop_test)
async def stop_test(message: types.Message, state: FSMContext):
    """
    Deactivates the test, and sends the results to users who have taken the test.
    """

    current_state = await state.get_state()
    if current_state is None:
        return

    if len(message.text) == 5 and message.text.isdigit():
        test_ = test.get_test(message.text)
        if test_ is not None:
            try:
                test.deactivate(test_['test_id'])
            except AttributeError:
                await message.reply(
                    f"{test_['test_id']} raqamli test allaqachon to'xtatilgan\!\n\n " \
                    f"{md.code('Owned by abduraxmonomonov.uz')}",
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
            else:
                dicted_answers = get_items_in_dict(str(test_['answers']).split(','))
                results = test_results.get_results(test_['test_id'])
                if results:
                    await send_test_results(message, test_, results, dicted_answers)
                    await state.finish()
                else:
                    await message.reply(
                        "Test yakunlandi natijalarni menyu orqali ko'rishingiz mumkin 🙂\n\n" \
                        f"{md.code('Owned by abduraxmonomonov.uz')}",
                        parse_mode=types.ParseMode.MARKDOWN_V2,
                    )
                    await state.finish()
        else:
            await message.reply(
                    f"{test_['test_id']} raqamli test mavjud emas\.\n\n" \
                    f"{md.code('Owned by abduraxmonomonov.uz')}",
                    parse_mode=types.ParseMode.MARKDOWN_V2,
                )
    else:
        await message.reply(
            "Test raqami 5ta sondan iborat 🤨\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


@dp.message_handler(Text(equals="Testni to'xtatish ⛔️"))
async def stop_test_state(message: types.Message):
    """
    Sets the STOP TEST state and tells the user to send the test id to stop that test.
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])

    if user is not None and (user['is_superuser'] is True or user['is_admin'] is True):
        await Form.stop_test.set()
        await message.reply(
            "Test raqamini yuboring\.\n\nEslatib o'taman test raqami 5ta sondan iborat\.\n\n%s" % \
            md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )
    else:
        await unknown_command(message)


# Assisting async functions
async def check_results(message: types.Message, test_id: str, answers: dict, correct_answers: dict):
    """
    Checks the test answers and returns correct and incorrect answers to a user.
    """

    user = user_model.get_user_or_users('chat_id', message.chat['id'])
    test_ = test.get_test(test_id)
    results = test_results.get_results(test_id)
    the_attended = []
    if results:
        for result in results:
            the_attended.append(result['test_taker'])
    incorrect_answers = list(answers.items() - correct_answers.items())
    correct_ones = len(correct_answers) - len(incorrect_answers)
    date_taken = time.strftime(r"%Y/%m/%d %H:%M:%S", time.localtime())
    if f"{user['first_name']} {user['last_name']}" not in the_attended:
        sk.get_supplies(
            'test_results',
            [
                'date_taken',
                'test_taker',
                'test_id',
                'test_subject',
                'questions_length',
                'correct_answers',
                'incorrect_answers',
                'user_answers',
            ],
            [
                date_taken,
                user['first_name'] + ' ' + user['last_name'],
                test_id,
                test_['test_subject'],
                len(str(test_['answers']).split(',')),
                correct_ones,
                len(incorrect_answers),
                ','.join([value for value in answers.values()]),
            ],
        )
    await message.reply(
            f"Test topshirilgan sana: {time.strftime(r'%Y/%m/%d %H:%M:%S', time.localtime())}\n" \
            f"Topshiruvchi: {user['last_name']} {user['first_name']}\n" \
            f"Test fani: {str(test_['test_subject']).title().replace('_', ' ')}\n\n" \
            f"Tog'ri javoblar soni: {correct_ones} ✅\n" \
            f"Noto'g'ri javoblar soni: {len(incorrect_answers)} ❌\n" \
            f"To'g'ri javoblar foizda: {int(get_percent(correct_ones, len(correct_answers)))}%\n" \
            f"Noto'g'ri javoblar foizda: {int(get_percent(len(incorrect_answers), len(correct_answers)))}%\n\n" \
            "Natijalaringiz haqida to'liq ma'lumotlar test yakunlanganidan so'ng yuboriladi\. " +
            "Testda ishtirok etganingiz uchun raxmat 🙂\n\n%s" % md.code("Owned by abduraxmonomonov.uz"),
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


async def get_test_answers(message: types.Message):
    """
    Tells a user how to send test answers.
    """

    await Form.test_check.set()
    text = "Javoblarni quyidagi ko'rinishda yuboring ⬇️\n\n"
    text2 = md.code("<test\_kodi\>:<fan\_nomi\>:javoblar\.\.\.\n\n")
    text3 = "Misol \-\> %s\n\n%s" % (md.code('12345:informatika:abcdabcdabcd...'), md.code('Owned by abduraxmonomonov.uz'))
    await message.reply(text + text2 + text3, parse_mode=types.ParseMode.MARKDOWN_V2)


async def no_names(message: types.Message):
    """
    Asks the user to provide their first and last names.
    """

    await Form.names.set()
    text = "Hurmatli foydalanuvchi botdan foydalanishni davom etish uchun " \
    "bir qancha ma'lumotlaringizni kiritishingiz lozim\. Keling birinchi " \
    "familiya va ismingizdan boshlaymiz\. Quyida keltirilgan misol kabi familiya va ismingizni kiriting\.\n\n" \
    "Misol \-\> %s\n\n%s\n\n%s" % \
    (
        md.code("f:Boltayev i:Bolta"), 
        md.underline("⚠️Familiya oldidan 'f:' va ism oldidan 'i:' belgilarini qo'yishni unutmang⚠️"), 
        str(md.code('Owned by abduraxmonomonov.uz')),
    )
    await message.reply(text, parse_mode=types.ParseMode.MARKDOWN_V2)


async def no_subscription(message: types.Message):
    """
    Asks the user to subscribe the channel.
    """

    latest_channel = channel.get_channel()

    text = "Hurmatli foydalanuvchi botdan foydalanishni davom etish uchun " \
    "quyida keltirilgan havola orqali kanalimizga obuna bo'lishingiz kerak\.\n\n%s" % md.code('Owned by abduraxmonomonov.uz')
    subscribe_url = 'https://t.me/' + str(latest_channel['username']).lstrip('@')
    subscribeBtns = InlineKeyboardMarkup()
    subscribeBtns.add(InlineKeyboardButton("Obuna bo'lish", subscribe_url))
    subscribeBtns.add(InlineKeyboardButton("Obuna bo'ldim ✅", callback_data=f"check_subscription:{message.chat['id']}"))
    await message.reply(text, parse_mode=types.ParseMode.MARKDOWN_V2, reply_markup=subscribeBtns)


async def send_test_results(
                    message: types.Message,
                    test_: dict, 
                    results: list | tuple,
                    dicted_answers: dict,
):
    """
    Sends test results to corresponding users.
    """

    for result in results:
        first_name = str(result['test_taker']).split()[0]
        last_name = str(result['test_taker']).split()[1]
        taker = user_model.get_user_by_name(first_name, last_name)
        user_answers = get_items_in_dict(str(result['user_answers']).split(','))
        correct_answers = list(user_answers.items() & dicted_answers.items())
        incorrect_answers = list(user_answers.items() - dicted_answers.items())
        str_cor_ans = ' ✅ '.join(sorted([f'{tup[0]}\. {str(tup[1]).upper()}' for tup in correct_answers]))
        str_inc_ans = ' ❌ '.join(sorted([f'{tup[0]}\. {str(tup[1]).upper()}' for tup in incorrect_answers]))
        str_cor_ans += ' ✅ '
        str_inc_ans += ' ❌ '
        msg_to_taker = f"{test_['test_id']} raqamli test yakunlandi\.\n\n" \
        f"Test topshiruvchi: {first_name} {last_name}\n" \
        f"To'g'ri javoblar\({len(correct_answers)}\):\n\n {str_cor_ans}\n\n" \
        f"Noto'g'ri javoblar\({len(incorrect_answers)}\):\n\n {str_inc_ans}\n\n" \
        f"{md.code('Owned by abduraxmonomonov.uz')}"
        await bot.send_message(taker['chat_id'], msg_to_taker, parse_mode=types.ParseMode.MARKDOWN_V2)
        await message.answer(
            "Test yakunlandi natijalarni menyu orqali ko'rishingiz mumkin 🙂\n\n" \
            f"{md.code('Owned by abduraxmonomonov.uz')}",
            parse_mode=types.ParseMode.MARKDOWN_V2,
        )


async def send_user_info(message: types.Message, user: dict):
    """
    Send user information to the request user.
    """

    changeUserInfoBtns = InlineKeyboardMarkup()

    changeUserInfoBtns.add(
        InlineKeyboardButton(
            "Familiya va ismni o'zgartirish ♻️", 
            callback_data='change_names',
        )
    )
    changeUserInfoBtns.add(
        InlineKeyboardButton(
            "Telefon raqamni o'zgaritirish ♻️", 
            callback_data='change_phone_number',
        )
    )
    changeUserInfoBtns.add(
        InlineKeyboardButton(
            "Manzilni o'zgartirish ♻️", 
            callback_data='change_address',
        )
    )
    changeUserInfoBtns.add(
        InlineKeyboardButton(
            "Maktabni o'zgartirish ♻️", 
            callback_data='change_school',
        )
    )
    changeUserInfoBtns.add(
        InlineKeyboardButton(
            "Sinfni o'zgartirish ♻️", 
            callback_data='change_class',
        )
    )
    username = '@' + user['username'] if user['username'] != "Mavjud emas" else md.underline(user['username'])
    await message.reply(
        f"Telegram hisobni tasdiqlovchi raqam \(id\): {md.underline(user['chat_id'])}\n" \
        f"Foydalanuvchi: {md.code(user['first_name'])} {md.code(user['last_name'])}\n" \
        f"Telefon raqam: {md.code(user['phone_number'])}\n" \
        f"Manzil: {md.code(user['address'])}\n" \
        f"Maktab: {md.code(user['school'])}\n" \
        f"Sinf: {md.code(user['class'])}\n" \
        f"Foydalanuvchi nomi: {username}\n\n" \
        f"{md.code('Owned by abduraxmonomonov.uz')}",
        parse_mode=types.ParseMode.MARKDOWN_V2,
        reply_markup=changeUserInfoBtns,
    )


async def show_appropriate_panel(message: types.Message, is_superuser: bool, is_admin: bool):
    """
    Shows the panel based on the user priviliges.
    """

    if is_superuser and is_admin:
        await message.answer(
            "Asosiy menyu 📋\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
            reply_markup=superuser_kb,
        )
    elif not is_superuser and is_admin:
        await message.answer(
            "Asosiy menyu 📋\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
            reply_markup=admin_kb,
        )
    else:
        await message.answer(
            "Asosiy menyu 📋\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
            parse_mode=types.ParseMode.MARKDOWN_V2,
            reply_markup=kb,
        )


async def unknown_command(message: types.Message):
    """
    Tells a user that the command they just sent does not exist.
    """

    await message.reply(
        "Mavjud bo'lmagan buyruq kiritildi\!\n\n%s" % md.code('Owned by abduraxmonomonov.uz'),
        parse_mode=types.ParseMode.MARKDOWN_V2,
    )


if __name__ == '__main__':
    executor.start_polling(dp)
