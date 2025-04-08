from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
)
from pyowm.owm import OWM
from datetime import datetime, timedelta, time


def get_weather(city) -> str:
    owm = OWM('')
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place( city )
    weather = observation.weather
    temp = weather.temperature( 'celsius' )
    wind = weather.wind()

    text = f"""На улице: {temp['temp']}°С,
    Облачность: {weather.status}/{weather.clouds},
    Влажность: {weather.humidity}%,
    Скорость ветра: {wind['speed']}м/с.
    """
    return text

async def send_weather(context: ContextTypes.DEFAULT_TYPE):
    print('отправляем сообщение')
    job = context.job
    await context.bot.send_message(job.chat_id, text=f'Погода в {job.data}:\n {get_weather(job.data)}')


async def select_city(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton('СПБ', callback_data='Санкт-Петербург'),
         InlineKeyboardButton('Москва', callback_data='Москва')],
        [InlineKeyboardButton('Казань', callback_data='Казань')],

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Город: ', reply_markup=reply_markup)

    return 'city_selected'


async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city = query.data
    context.bot_data['city'] = city
    keyboard = [
        [InlineKeyboardButton('Через 1ч', callback_data=3600),
         InlineKeyboardButton('На 8ч утра', callback_data=8),
         InlineKeyboardButton('На 13ч дня', callback_data=13),
         InlineKeyboardButton('На 18ч вечера', callback_data=18)],
        [InlineKeyboardButton('Узнать сейчас', callback_data=1)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text('Время:', reply_markup=reply_markup)
    return 'time_selected'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_message.chat_id

    query = update.callback_query
    city = context.bot_data['city']
    gettime = int(query.data)
    nowor1hour = False# хранит выбран ли узнать сейчас или 1ч
    # et = end time время на которое установлен таймер
    if gettime == '8':
        et = 8
        nowor1hour = True
    if gettime == '13':
        et = 13
        nowor1hour = True
    if gettime == '18':
        et = 18
        nowor1hour = True


    now = datetime.now()
    if nowor1hour == True:
        if now.time() > time(et):

            tomorrow = now + timedelta(days=1)

            target_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, et)
            enter_time = target_time - now
        else:
            timer_time = datetime.combine(now.date(), time(et, 0, 0))
            enter_time = timer_time - now

    else:
        enter_time = int(gettime)

    context.job_queue.run_once( send_weather, enter_time, chat_id=chat_id, name=str( chat_id ), data=city )
    print('timer set')


def main():
    application = Application.builder().token("").build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('hello', select_city)],
        states={
            'city_selected': [
                CallbackQueryHandler(select_time)
            ],
            'time_selected': [
                CallbackQueryHandler(start)
            ]
        },
        fallbacks=[CommandHandler('hello', select_city)],
    ))
    application.run_polling()


if __name__ == '__main__':
    main()