from abc import ABC, abstractmethod

from playwright.async_api import async_playwright, Page, BrowserContext

from pprint import pprint

from .helpers import check_valid_event
from .proxy_manager import ProxyManager
from loguru import logger


class BaseParser(ABC):
    def __init__(self, start_url: str, event_filter: str, all_user_data: dict):
        self.start_url: str = start_url
        self.event_filter: str = event_filter
        self.all_user_data: dict = all_user_data
        self.payment_link = None
        self.context = None

        self.year_month: list[str] = ['2024.11', '2024.12', '2025.01']
        self.event_name: str = event_filter[0]
        self.event_date: str = event_filter[1]

        self.event_id = None
        self.show_id = None
        self.company_id = None
        self.spa_session = None

    # complete
    @abstractmethod
    async def check_relevant_tickets(self, p: Page) -> None:
        """
            Finds links to events for which there are tickets.

        :param p: Page
        :return: None
        """
        ...

    @abstractmethod
    async def get_tickets(self, p: Page) -> list[dict]:
        """
            Finds available tickets for a given event.

        :param p: Page
        :param context: BrowserContext
        :return: Dictionary with tickets data
        """
        ...

    @abstractmethod
    async def create_basket_items(self, p: Page, data: list[dict]):
        """
            A function that adds valid tickets to the payment cart

        :param p: Page
        :param data: List of dictionaries with ticket data
        :return: None
        """
        ...

    async def get_spa_session(self, p: Page) -> None:
        """
            The function that receives the site session token.
        :param p: Page
        :return: None
        """
        response = await (await p.request.post(
            url=f"https://widget.profticket.ru/api/basket/start-session/?language=ru-RU",
            data={'company_id': self.company_id}
        )).json()
        self.spa_session = response['response']['session']

    @abstractmethod
    async def send_payment_link(self) -> None:
        """
            Sends a payment link in a telegram to a specific person.

        :return: None
        """
        ...

    async def run_parser(self) -> None:
        """
            The parsing manager.
        :return: None
        """
        while True:
            if await check_valid_event(self.all_user_data):
                logger.warning(f'Event disable, stop parsing! {self.event_filter}')
                return
            async with async_playwright() as p:
                proxy_manager = ProxyManager()
                logger.success('Start session')

                async for item in proxy_manager.get_proxy_for_request():
                    try:
                        browser = await p.chromium.launch()
                        context = await browser.new_context(
                            proxy=item,
                            viewport={
                                'width': 1920,
                                'height': 1080
                            },
                            user_agent=proxy_manager.user_agent
                        )
                        page = await context.new_page()
                        logger.success(f'Relevant proxy - {item["server"]}')
                        logger.success('Create context')

                        self.context = context
                        await self.check_relevant_tickets(p=page)

                        # self.event_id = '6861'
                        # self.show_id = '5233'
                        # self.company_id = '54'
                        if not self.show_id and not self.company_id:
                            break
                        purchase_tickets: list[dict] = await self.get_tickets(p=page)

                        print(purchase_tickets)

                        if purchase_tickets:
                            await self.create_basket_items(p=page, data=purchase_tickets)

                            print(await self.context.cookies())

                        break
                    except Exception as ex:
                        if "net::ERR_TIMED_OUT" in ex.__str__():
                            logger.warning(f'An irrelevant proxy - {item["server"]}')
                            continue
                        raise Exception(ex)
                break
            break


__all__ = [
    'BaseParser'
]