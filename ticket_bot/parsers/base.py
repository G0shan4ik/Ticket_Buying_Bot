from abc import ABC, abstractmethod

from playwright.async_api import async_playwright, Page, BrowserContext

from pprint import pprint

from .proxy_manager import ProxyManager
from loguru import logger


class BaseParser(ABC):
    def __init__(self, start_url: str, event_filter: list[str]):
        self.start_url: str = start_url
        self.event_filter: list[str] = event_filter
        self.payment_link = None
        self.context = None

        self.year_month: list[str] = ['2024.11', '2024.12', '2025.01']
        self.event_name: str = event_filter[0]
        self.event_date: str = event_filter[1]

        self.event_id = None
        self.show_id = None
        self.company_id = None

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
    async def get_tickets(self, p: Page, context: BrowserContext) -> list[dict]:
        """
            Finds available tickets for a given event.

        :param p: Page
        :param context: BrowserContext
        :return: Dictionary with tickets data
        """
        ...
    # @abstractmethod
    # async def choose_and_pay_tickets(self, p: Page):
    #     """
    #         Selects tickets by filter from the available tickets on the website and
    #     adds them to the "payment".
    #         Fills out the payment form and goes to the payment system and
    #     pulls out a link to pay for tickets.
    #
    #     :param p: Page
    #     :return: Payment link
    #     """
    #     ...
    # https://widget.profticket.ru/api/event/scheme/?company_id=54&global_show_id=5233&event_id=6861&language=ru-RU
    # ссылка где которая возвращает json с местами посадки, там можно найти доступные и из них вибирать
    #
    # https://widget.profticket.ru/api/basket/pre-reservation/?language=ru-RU - post запрос со страницы с мероприятием на оформление заказа
    # [{"event_id":"6862","set_id":null,"cod_sec":"186","row":"5","seat":"18","price":2500,"price_sell":2500},{"event_id":"6862","set_id":null,"cod_sec":"186","row":"4","seat":"1","price":2500,"price_sell":2500}]
    #
    # @abstractmethod
    # async def send_payment_link(self, p: Page) -> None:
    #     """
    #         Sends a payment link in a telegram to a specific person.
    #
    #     :param p: Page
    #     :return: None
    #     """
    #     ...

    async def run_parser(self) -> None:
        """
            The parsing manager.
        :return: None
        """
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
                    self.context = context
                    page = await context.new_page()
                    logger.success(f'Relevant proxy - {item["server"]}')
                    logger.success('Create context')

                    # await self.check_relevant_tickets(p=page)

                    self.event_id = '6861'
                    self.show_id = '5233'
                    self.company_id = '54'

                    purchase_tickets: list[dict] = await self.get_tickets(p=page, context=context)
                    if purchase_tickets:
                        ...

                    break
                except Exception as ex:
                    if "net::ERR_TIMED_OUT" in ex.__str__():
                        logger.warning(f'An irrelevant proxy - {item["server"]}')
                        continue
                    raise Exception(ex)


__all__ = [
    'BaseParser'
]