from .include import *


@router.message(Command(commands=['help']))
async def delete_link(message: Message):
    await message.answer(
        text=HELP_TEXT
    )
