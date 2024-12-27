import asyncio
import random
from random import randint

from loguru import logger
from aiogram import Bot
from json import dumps

from .base import BaseParser
from .helpers import get_fake_data
from .captcha import CaptchaMixin


class BuyingTicketsNikulina(BaseParser, CaptchaMixin):
    def __init__(self, event_filter: list, all_user_data: dict, bot: Bot):
        super().__init__(
            event_filter=event_filter,
            all_user_data=all_user_data,
            start_url="https://spa.profticket.ru/customer/53/shows",
            bot=bot,
            company_id = 53,
            venue='Цирк Никулина'
        )
        CaptchaMixin.__init__(self)
        self.venue = 'Цирк Никулина'

    def reformat_sectors(self, sector_name: str) -> bool:
        """
            Returns True if the sector_name matches the filter
        :param sector_name: Sector name (str)
        :return: bool
        """
        if len(self.event_filter) <= 2 or self.event_filter[2].lower() == 'все значения':
            return True
        elif ',' in self.event_filter[2]:
            rng = self.event_filter[2].lower().split(', ')
            if sector_name in [i.strip().lower() for i in rng]:
                return True
        elif sector_name.lower() == self.event_filter[2].lower():
            return True
        return False

    def reformat_rows_or_seats(self, rows_seats: str, rows_seats_name: str) -> bool:
        """
            Returns True if the rows_seats matches the filter.

        :param rows_seats: value: 'rows' or 'seats'
        :param rows_seats_name: number rows or seats
        :return: bool
        """
        num = 3 if rows_seats == 'rows' else 4
        if len(self.event_filter) <= 3 or self.event_filter[num].lower() == 'все значения':
            return True
        elif '-' in self.event_filter[num]:
            rng = self.event_filter[num].split('-')
            if int(rows_seats_name) in [i for i in range(int(rng[0]), 1 + int(rng[-1]))]:
                return True
        elif ',' in self.event_filter[num] or len(self.event_filter[num]) >= 1:
            rng = self.event_filter[num].split(',')
            if int(rows_seats_name) in [int(i) for i in rng]:
                return True
        return False

    async def check_relevant_tickets(self) -> None:
        self.show_id, self.event_id, self.global_show_id = None, None, None

        await self.session.goto(url=self.start_url, wait_until='commit')

        logger.success(f'Start pars {self.start_url}, {self.venue}.')

        for i in self.year_month:
            try:
                response = await (await self.session.request.get(
                    url=f"https://widget.profticket.ru/api/event/list/?company_id=53&type=events&page=1&period_id=4&date={i}&language=ru-RU"
                )).json()
            except:
                logger.warning(f'Invalid year.month {i}')
                continue

            await asyncio.sleep(0)

            logger.info(f'Pars event for {i}, {self.venue}.')

            all_page_events = response['response']['items']
            for item in all_page_events:
                for event in item['events']:
                    if event['free_places_count']:
                        date_formatted = ' '.join(event['show']['first_event_date_formatted'].replace(',', '')).replace(' ', '')

                        if (self.event_name.lower() == event['show_name'].lower() and
                                self.event_date.replace(' ', '') == date_formatted):
                            self.event_id = event['id']
                            self.show_id = event['show']['id']
                            self.global_show_id = event['show_id']

                            await self.get_spa_session()
                            return
                await asyncio.sleep(0)
        logger.warning(f'No tickets were found for the <- {self.event_name, self.event_date} -> event!')

    async def get_tickets(self) -> list[dict]:
        scheme_url = (f'https://widget.profticket.ru/api/event/scheme/?company_id={self.company_id}&'
                      f'global_show_id={self.show_id}&event_id={self.event_id}&language=ru-RU')
        response = await (await self.session.request.get(
            url=scheme_url
        )).json()
        await asyncio.sleep(0)

        result_data: list[dict] = []
        all_event_tickets = response['response']['items']

        for ticket in all_event_tickets:
            if ticket['price']:
                if (self.reformat_sectors(sector_name=ticket['name_sec'].lower()) and
                    self.reformat_rows_or_seats(rows_seats='rows', rows_seats_name=ticket['row']) and
                        self.reformat_rows_or_seats(rows_seats='seats', rows_seats_name=ticket['seat'])
                ):
                    result_data.append(
                        {
                            "event_id": ticket['event_id'],
                            "set_id": ticket['set_id'],
                            "cod_sec": ticket['cod_sec'],
                            "row": ticket['row'],
                            "seat": ticket['seat'],
                            "price": ticket['price'],
                            "price_sell": ticket['price_sell'],
                        }
                    )
        logger.info(f'Pars valid tickets for event: {self.event_name}')
        return result_data

    async def create_basket_items(self, data: list[dict]) -> bool:
        response = await (await self.session.request.post(
            url=f"https://widget.profticket.ru/api/basket/pre-reservation/?language=ru-RU",
            data={
                'session': self.spa_session,
                'company_id': self.company_id,
                'global_show_id': self.show_id,
                'items': dumps(data)
            }
        )).json()

        if 'error' in str(response) and "'code': 15" in str(response):
            await self.solve_captcha(
                session=self.session,
                company_id=self.company_id,
                show_id=self.global_show_id,
                event_id=self.event_id,
                key=response['error']['message']['siteKey']
            )
            await (await self.session.request.post(
                url=f"https://widget.profticket.ru/api/basket/pre-reservation/?language=ru-RU",
                data={
                    'session': self.spa_session,
                    'company_id': self.company_id,
                    'global_show_id': self.show_id,
                    'items': dumps(data)
                }
            )).json()

        logger.info(f"Create basket items for event (add {len(data)} tickets): {self.event_name}")
        return True

    async def pars_payment_link(self):
        fake_data = await get_fake_data(mail=self.mail)
        analytics_id = f'{random.randint(472425213, 2071200932)}.17{randint(12645897, 98765433)}'

        response = await (await self.session.request.post(
            'https://widget.profticket.ru/api/order/create/?language=ru-RU',
            data={
                'session': self.spa_session,
                'company_id': self.company_id,
                'user_name': fake_data[0],
                'user_phone': fake_data[1],
                'user_email': fake_data[-1],
                'gift_recipient_name': '',
                'accepted': 1,
                'custom_checkbox': '',
                'analytics_client_id': analytics_id,
                'payment_system_id': 335,
                'visitors_data': []
            }
        )).json()
        self.payment_link = response['response']['payment_url']
        logger.success(f"Success pars payment link({self.payment_link}) for event: {self.event_name}")