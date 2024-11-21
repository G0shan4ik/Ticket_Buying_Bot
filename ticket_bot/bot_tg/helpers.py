import json
import aiofiles
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from loguru import logger


async def read_data_from_json(file_name: str = 'users_filters.json') -> list[dict] | None:
    """
        Async function for reading data from a JSON file.
    :param file_name: (str, optional):  Defaults to 'users_filters.json'.
    :return: Dictionaries read from the file.
    """
    try:
        async with aiofiles.open(file_name, 'r', encoding='utf-8') as file:
            data = await file.read()
            return json.loads(data)
    except json.decoder.JSONDecodeError:
        logger.warning(f'{file_name}.json is empty!')
        return None

async def write_data_to_json(data: dict|list[dict], file_name: str = 'users_filters.json', change: bool=False) -> None:
    """
        A function that adds a dictionary with data.json data
    :param data: Dictionaries to write.
    :param file_name: (str, optional):  Defaults to 'users_filters.json'.
    :param change: Used if you need to overwrite json
    :return: None
    """
    current_data: list[dict] = await read_data_from_json()

    async with aiofiles.open(file_name, 'w', encoding='utf-8') as file:
        if change and isinstance(data, list):
            await file.write(f"{json.dumps(data, indent=4, ensure_ascii=False)}")
            return

        if current_data:
            current_data.append(data)
            await file.write(f"{json.dumps(current_data, indent=4, ensure_ascii=False)}")
        else:
            await file.write(f"[\n{json.dumps(data, indent=4, ensure_ascii=False)}\n]")


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Cancel")]],
        resize_keyboard=True,
        one_time_keyboard=True
        )

def check_valid_filter_format(filter_string: str) -> list[str] | None:
    filter_string: list[str] = [i.lower().strip() for i in filter_string.split(';')]
    if '' in filter_string:
        filter_string.remove('')

    if len(filter_string) >= 3:
        if '-' in filter_string:
            filter_string.remove('-')
        return filter_string
    return

def delete_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Удалить ссылку💣', callback_data='delete')]
        ]
    )

async def delete_link(user_id: int) -> None:
    data: list[dict] = await read_data_from_json()
    for item in data:
        for _id, value in item.items():
            if int(_id) == user_id:
                value[-1] = 'disabled'
    await write_data_to_json(data, change=True)
