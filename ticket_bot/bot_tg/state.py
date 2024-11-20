from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from .core import router
from .helpers import check_valid_filter_format, write_data_to_json
from ticket_bot.parsers.parser import BuyingTicketsNikulina


class AddParsFilter(StatesGroup):
    add_filter = State()


@router.message(F.text == 'Cancel')  # exit the state
async def exit_the_state(message: Message, state: FSMContext):
    await message.answer(
        text='⛔️Вы прервали заполнение фильтра.',
        reply_markup=None
    )
    await state.clear()

@router.message(AddParsFilter.add_filter, F.text)
async def add_link_(message: Message, state: FSMContext):
    data: list[str] = check_valid_filter_format(filter_string=message.text)
    if data is None:
        await message.answer('❗️ Вы ввели некорректный формат фильтра ❗️')
        await state.set_state(AddParsFilter.add_filter)
        return

    await write_data_to_json(
        {message.from_user.id: [data, 'active']}
    )
    await message.answer(
        text='✅Фильтр успешно установлен!',
    )

    await state.clear()

    # тут будет отрабатывать run_parser()
    # start = BuyingTicketsNikulina(event_filter=data)
    # await start.run_parser()

