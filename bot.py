from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from settings import bot_config
from parse_gost.gost import Gost, logger

bot = Bot(token=bot_config.bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    text = f'Привет, я бот, который поможет тебе легко и быстро скачать нужный стандарт с protect.gost.ru.\n' \
           f'Скинь мне пожалуйста ссылку на страницу со страницами стандарта и через запятую напиши его название.'
    await message.answer(text)


@dp.message_handler()
async def url_message(message: types.Message):
    url, name = message.text.split(', ')
    try:
        Gost(url, name).get()
        logger.info('get Gost >>> done')
        try:
            await message.reply_document(open(f'{name}_1.pdf', 'rb'))
            await message.reply_document(open(f'{name}_2.pdf', 'rb'))
        except:
            await message.reply_document(open(f'{name}.pdf', 'rb'))
    except Exception as err:
        await message.answer(f'Ох, что-то не получается :(\nОшибка: {err}\nНапишите @metravod, он поможет')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
