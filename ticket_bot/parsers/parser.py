import asyncio
from pprint import pprint

from loguru import logger
from .base import BaseParser
from playwright.async_api import Page
from aiogram import Bot


class BuyingTicketsNikulina(BaseParser):
    def __init__(self, event_filter: str, all_user_data: dict, bot: Bot):
        super().__init__(
            event_filter=event_filter,
            all_user_data=all_user_data,
            start_url="https://spa.profticket.ru/customer/53/shows",
            bot=bot,
            company_id = 53
        )
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


    async def check_relevant_tickets(self, p: Page) -> None:
        self.show_id, self.event_id = None, None

        await p.goto(url=self.start_url, wait_until='commit')

        logger.success(f'Start pars {self.start_url}, {self.venue}.')

        for i in self.year_month:
            try:
                response = await (await p.request.get(
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

                            await self.get_spa_session(p=p)
                            return
                await asyncio.sleep(0)
        logger.warning(f'No tickets were found for the <- {self.event_name, self.event_date} -> event!')

    async def get_tickets(self, p: Page) -> list[dict]:
        scheme_url = (f'https://widget.profticket.ru/api/event/scheme/?company_id={self.company_id}&'
                      f'global_show_id={self.show_id}&event_id={self.event_id}&language=ru-RU')
        response = await (await p.request.get(
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
        return result_data

    async def create_basket_items(self, p: Page, data: list[dict]) -> None:
        response = await (await p.request.post(
            url=f"https://widget.profticket.ru/api/basket/pre-reservation/?language=ru-RU",
            data={
                'session': self.spa_session,
                'company_id': self.company_id,
                'global_show_id': self.show_id,
                'items': data
            }
        )).json()
        pprint(response)


if __name__ == '__main__':
    # from pprint import pprint

    # https://payecom.ru/pay?orderId=951ca526-fc94-5fd7-1a63-ea6037b2df93
    #                        orderId=951ca526-fc94-5fd7-1a63-ea6037b2df93
                                    #ddf6b230-a1ca-4beb-91d7-38deb2fad8e5
    # https://payecom.ru/pay?orderId=bf154057-8f4c-5e77-1fb6-e14fcde4c5b8
    # async def main():
    #     per = BuyingTicketsNikulina(
    #         event_filter=['https://widget.profticket.ru', '', '', ''],
    #     )
    #     await per.run_parser()
    #
    # asyncio.run(main())
    # event_filter = ['Матрешка', '16 ноя 2024 14:00', 'Амфитеатр Правая сторона, артер', '3-4', 'все значения']
    # def reformat_sectors():
    #     if len(event_filter) <= 2 or event_filter[2] == 'все значения':
    #         return 'все значения'
    #     elif ',' in event_filter[2]:
    #         rng = event_filter[2].split(',')
    #         return [i.strip() for i in rng]
    #     return event_filter[2]
    #
    # print(reformat_sectors())

    ...