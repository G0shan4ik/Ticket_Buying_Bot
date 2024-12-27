from random import choice

from ticket_bot.bot_tg.helpers import read_data_from_json
from faker import Faker
import aiofiles


async def get_random_email():
    async with aiofiles.open("all_emails.txt", 'r', encoding='utf-8') as file:
        data = (await file.read()).split('\n')
        return choice(data).split(':')[0]


async def get_fake_data(mail: str, locale: str='ru_RU') -> list[str]:
    """
        Create fake login details for the ticket payment form
    :param mail: users email
    :param locale: optional parameter
    :return: returns a list containing 3 lines [fake_name, fake_phone_number, fake_email]
    """
    fake = Faker(locale=locale)
    phone = fake.phone_number()

    for item in ['+', '-', '(', ')', ' ']:
        phone = phone.replace(item, '')

    return [
        fake.name(),
        phone.strip(),
        mail
    ]


async def check_valid_event(data: dict) -> bool:
    """
        A function that checks the event for activity
    :param data: { 'user_id': [ filter_data ], 'active/disable' }
    :return: Returns True if the event is not disabled
    """
    all_data = await read_data_from_json()
    if data in all_data:
        return True
    return False

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]