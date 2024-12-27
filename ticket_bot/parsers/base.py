import asyncio
from abc import ABC, abstractmethod

from aiogram.utils.markdown import hbold
from playwright.async_api import async_playwright

from .helpers import check_valid_event, chunks, get_random_email
from .proxy_manager import ProxyManager
from loguru import logger

from aiogram import Bot

from os import getenv
from dotenv import load_dotenv

load_dotenv()


group_id = getenv('GROUP_ID')


class BaseParser(ABC):
    def __init__(self, start_url: str, event_filter: list, all_user_data: dict, bot: Bot, company_id: int, venue: str):
        self.start_url: str = start_url
        self.event_filter: list = event_filter
        self.all_user_data: dict = all_user_data
        self.bot = bot
        self.payment_link = ''
        self.context = None
        self.session = None

        self.year_month: list[str] = ['2024.12', '2025.01', '2025.02', '2025.03', '2025.04']
        self.event_name: str = event_filter[0]
        self.event_date: str = event_filter[1]

        self.company_id = company_id
        self.event_id = None
        self.show_id = None
        self.global_show_id = None
        self.spa_session = None
        self.mail = None
        self.venue = venue

        self.delay = 1200

    @staticmethod
    def get_bought_tickets(data: list[dict]) -> str:
        result = str()
        for item in data:
            result += f'--Ряд {item["row"]}, Место {item["seat"]}, {item["price"]} руб.\n'
        return result

    def __repr__(self):
        _formatted_date = self.event_date.split()
        _formatted_date[1] = _formatted_date[1][:3].capitalize()
        return \
            f'''{self.event_name.capitalize()}, {' '.join(_formatted_date)}\n''' \
            f'''{hbold("Сектор:")} {self.event_filter[2].capitalize()}\n&&&''' \
            f'''{self.payment_link}\n''' \
            f'''{hbold("Схема:")} https://spa.profticket.ru/customer/{self.company_id}/shows/{self.global_show_id}/#{self.event_id}\n''' \
            f'''{hbold("Account:")} {self.mail}'''

    # @staticmethod
    # async def get_all_tickets_amount():
    #     async with aiofiles.open('amount.txt', 'r', encoding='utf-8') as file:
    #         try:
    #             num = (await file.read()).replace('\n', '')
    #             return int(num)
    #         except Exception as ex:
    #             logger.error(f'{ex}\n\n')
    #             if 'invalid literal for int() with base 10:' in str(ex):
    #                 return 0


    # async def plus_one_ticket(self):
    #     old_amount = await self.get_all_tickets_amount()
    #     async with aiofiles.open('amount.txt', 'w', encoding='utf-8') as file:
    #         await file.write(str(old_amount + 1))

    @abstractmethod
    async def check_relevant_tickets(self) -> None:
        """
            Finds links to events for which there are tickets.

        :return: None
        """
        ...

    @abstractmethod
    async def get_tickets(self) -> list[dict]:
        """
            Finds available tickets for a given event.
        :return: Dictionary with tickets data
        """
        ...

    @abstractmethod
    async def create_basket_items(self, data: list[dict]) -> bool:
        """
            A function that adds valid tickets to the payment cart
        :param data: List of dictionaries with ticket data
        :return: None
        """
        ...

    @abstractmethod
    async def pars_payment_link(self) -> None:
        """
            A function that pars a link to the Sberbank payment system.
        :return: None
        """
        ...

    async def get_spa_session(self) -> None:
        """
            The function that receives the site session token.
        :return: None
        """
        response = await (await self.session.request.post(
            url=f"https://widget.profticket.ru/api/basket/start-session/?language=ru-RU",
            data={'company_id': self.company_id}
        )).json()
        self.spa_session = response['response']['session']

    async def send_payment_link(self, data: list[dict]) -> None:
        """
            Sends a payment link in a telegram to a specific person.
        :return: None
        """
        _tickets = self.get_bought_tickets(data=data)
        txt = self.__repr__().split('&&&')

        await self.bot.send_message(
            chat_id=self.all_user_data['user_id'],
            # chat_id=group_id,
            text=f'{txt[0]}{_tickets}{txt[-1]}' # [#{hbold(await self.get_all_tickets_amount())}]\n
        )
        # await self.plus_one_ticket()
        self.payment_link = ''

    async def run_parser(self) -> None:
        """
            The parsing manager.
        :return: None
        """
        while True:
            try:
                async with async_playwright() as p:
                    proxy_manager = ProxyManager()
                    logger.success('Start session')

                    if await check_valid_event(self.all_user_data):
                        logger.warning(f'Event disable, stop parsing! {self.event_filter}')
                        return

                    async for item in proxy_manager.get_proxy_for_request():
                        self.mail = await get_random_email()
                        try:
                            browser = await p.chromium.launch()
                            context = await browser.new_context(
                                proxy=item,
                                viewport={
                                    'width': 1920,
                                    'height': 1080
                                },
                                user_agent=proxy_manager.user_agent,
                                base_url='https://spa.profticket.ru',

                            )
                            self.session = await context.new_page()
                            logger.success('Create context')

                            response = await self.session.request.get(
                                'https://spa.profticket.ru/customer/53/shows'
                            )
                            if response.status not in [200, 201, 202, 203, 204]:
                                logger.warning('INVALID PROXY')
                                continue

                            self.context = context
                            await self.check_relevant_tickets()
                            await asyncio.sleep(0)
                            logger.success(f'Relevant proxy - {item["server"]}')

                            if not self.show_id and not self.company_id:
                                logger.error(f'!SIMPLE! block proxi {item["server"]}')
                                continue
                            purchase_tickets: list[dict] = await self.get_tickets()

                            # print(purchase_tickets)

                            if purchase_tickets:
                                for stack in [i for i in chunks(purchase_tickets, 5)]:
                                    try:
                                        if await self.create_basket_items(data=stack):
                                            await self.pars_payment_link()
                                            await self.send_payment_link(data=stack)
                                        else:
                                            raise Exception('Artificial exclusion (block "user")')
                                    except Exception as ex:
                                        logger.error(f'{ex}\n\n')
                                        continue
                            logger.warning(f'All tickets bought for event {self.event_name}, {self.event_date}')
                            logger.info(f'Wait {self.delay} seconds ({self.delay // 60} minutes)')
                            await asyncio.sleep(self.delay)
                        except Exception as ex:
                            if "net::ERR_TIMED_OUT" in ex.__str__():
                                logger.warning(f'An irrelevant proxy - {item["server"]}')
                                continue
                            raise Exception(ex)
            except Exception as ex:
                logger.error(f"{ex}")
                continue

__all__ = [
    'BaseParser'
]