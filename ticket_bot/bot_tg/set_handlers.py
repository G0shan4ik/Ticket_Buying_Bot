from aiogram.fsm.context import FSMContext

from .state import AddParsFilter
from .include import *
from .helpers import cancel_kb



@router.message(Command(commands=['add_filter']))
async def delete_link(message: Message, state: FSMContext):
    await message.answer(
        text=FILTER_HELP_TEXT,
        reply_markup=cancel_kb()
    )
    await state.set_state(AddParsFilter.add_filter)

