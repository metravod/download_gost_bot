from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from settings import bot_config
from parse_gost.gost import Gost, logger

bot = Bot(token=bot_config.bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    text = f'Привет, я бот, который поможет тебе легко и быстро скачать нужный стандарт с protect.gost.ru'
    await message.answer(text)


@dp.message_handler()
async def url_message(message: types.Message):
    url, name = message.text.split(', ')
    Gost(url, name).get()
    logger.info('get Gost >>> done')
    await message.reply_document(open(f'{name}.pdf', 'rb'))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
