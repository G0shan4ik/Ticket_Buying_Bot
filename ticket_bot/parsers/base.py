import asyncio
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright

from .helpers import check_valid_event, chunks
from .proxy_manager import ProxyManager
from loguru import logger

from aiogram import Bot

from random import randint


class BaseParser(ABC):
    def __init__(self, start_url: str, event_filter: list, all_user_data: dict, bot: Bot, company_id: int):
        self.start_url: str = start_url
        self.event_filter: list = event_filter
        self.all_user_data: dict = all_user_data
        self.bot = bot
        self.payment_link = ''
        self.context = None
        self.session = None

        self.year_month: list[str] = ['2024.12', '2025.01', '2025.02']
        self.event_name: str = event_filter[0]
        self.event_date: str = event_filter[1]

        self.company_id = company_id
        self.event_id = None
        self.show_id = None
        self.spa_session = None

        self.delay = 900

    # complete
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

    async def send_payment_link(self) -> None:
        """
            Sends a payment link in a telegram to a specific person.
        :return: None
        """
        await self.bot.send_message(
            chat_id=self.all_user_data['user_id'],
            text=self.payment_link
        )
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
                                for stack in [i for i in chunks(purchase_tickets, 3)]:
                                    try:
                                        if await self.create_basket_items(data=stack):
                                            logger.info('Sleep between buy tickets')
                                            await asyncio.sleep(randint(45, 69))
                                            await self.pars_payment_link()
                                            await self.send_payment_link()
                                        else: raise Exception('Artificial exclusion (block proxi)')
                                    except Exception as ex:
                                        logger.error(f'Block proxi {item["server"]} !WHEN BUYING TICKETS!')
                                        continue
                            logger.warning(f'All tickets bought for event {self.event_name}, {self.event_date}')
                            logger.info(f'Wait {self.delay} seconds ({self.delay / 60}minutes)')
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