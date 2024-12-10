from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from .state import AddParsFilter
from .include import *
from .helpers import cancel_kb, read_data_from_json, delete_kb, delete_link

from .core import bot_


@router.message(Command(commands=['add_filter']))
async def add_filter(message: Message, state: FSMContext):
    await message.answer(
        text=FILTER_HELP_TEXT,
        reply_markup=cancel_kb()
    )
    await state.set_state(AddParsFilter.add_filter)

@router.message(Command(commands=['all_filters']))
async def get_all_filters(message: Message):
    data: list[dict] = await read_data_from_json()
    fl = True
    if data:
        for item in data:
            for _id, value in item.items():
                if int(_id) == message.from_user.id and value[-1] == 'active':
                    fl = False
                    await message.answer(
                        text=hbold(*[f'{i.capitalize()}, ' for i in value[0]]),
                        reply_markup=delete_kb()
                    )
    if fl:
        await message.answer(hbold('❕У вас нет установленных фильтров.'))

@router.callback_query(lambda query: query.data.startswith('delete'))
async def next_photo_filter(query: CallbackQuery):
    user_id = query.from_user.id
    await delete_link(user_id=user_id)
    await bot_.delete_message(
        chat_id=query.message.chat.id,
        message_id=query.message.message_id
    )
    await query.answer('Ссылка удалена 💥')