from datetime import datetime

from faker import Faker


def get_fake_data(locale: str='ru_RU') -> list[str]:
    """
        Create fake login details for the ticket payment form
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
        fake.email(domain='gmail.com')
    ]


