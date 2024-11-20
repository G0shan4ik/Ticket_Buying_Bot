import json
import aiofiles
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from loguru import logger


async def read_data_from_json(file_name: str = 'data.json') -> list[dict] | None:
    """
        A function that reads the contents of the data.json file.
    :param file_name:
    :return: List of dictionaries { event: str, date: str, sectors: str, rows: str, seats: str }
    """
    try:
        async with aiofiles.open(file_name, 'r', encoding='utf-8') as file:
            data = await file.read()
            return json.loads(data)
    except json.decoder.JSONDecodeError:
        logger.warning(f'data.json is empty!')
        return None

async def write_data_to_json(data: dict, file_name: str = 'data.json') -> None:
    """
        A function that adds a dictionary with data.json data
    :param data: pattern { event: str, date: str, sectors: str, rows: str, seats: str }
    :param file_name:
    :return: None
    """
    current_data = await read_data_from_json()
    async with aiofiles.open(file_name, 'w', encoding='utf-8') as file:
        if current_data:
            current_data.append(data)
            await file.write(f"{json.dumps(current_data, indent=4, ensure_ascii=False)}")
        else:
            await file.write(f"[{json.dumps(data, indent=4, ensure_ascii=False)}]")

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

if __name__ == '__main__':
    ...