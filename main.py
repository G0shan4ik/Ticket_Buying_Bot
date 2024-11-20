from ticket_bot.bot_tg.core import start_bot

import sys
import logging
import asyncio

from loguru import logger


def start_dev() -> None:
    logger.success('The program is running')
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    try:
        asyncio.run(start_bot())
    except (asyncio.exceptions.CancelledError, KeyboardInterrupt):
        logger.info('The bot was forcibly stopped')