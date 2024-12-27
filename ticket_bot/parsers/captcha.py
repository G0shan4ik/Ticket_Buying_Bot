from playwright.async_api import Page
from twocaptcha import TwoCaptcha
from loguru import logger

from os import getenv
from dotenv import load_dotenv


load_dotenv()


__all__ = ["CaptchaMixin"]


class CaptchaMixin:
    def __init__(self):
        if getenv("API_KEY_RUCAPTCHA") is None:
            raise ValueError("No API_KEY_RUCAPTCHA in environment")
        self._solver = TwoCaptcha(getenv("API_KEY_RUCAPTCHA"))

    async def solve_captcha(self, session: Page, key: str, company_id, show_id, event_id) -> bool:
        """
        Solves a captcha
        """
        try:
            show_id = 94
            solved_key = self._solver.solve_captcha(
                site_key=key,
                page_url=f'https://spa.profticket.ru/customer/{company_id}/shows/{show_id}?eventsIds%5B%5D={event_id}',
            )
            if not solved_key:
                raise Exception('Artificial exclusion (The captcha has not been solved)')

            await (await session.request.post(
                'https://widget.profticket.ru/api/anti-fraud/verify-captcha/?language=ru-RU',
                data={
                    'company_id': company_id,
                    'token': solved_key
                }
            )).json()

            logger.success(f'Success solved captcha')

        except Exception as ex:
            logger.error(f'The captcha has not been solved\n{ex}\n\n')
            return False

        logger.success(f'STATUS SOLVED CAPTCHA')
        return True