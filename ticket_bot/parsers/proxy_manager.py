import json
import aiofiles
from loguru import logger

import re

from typing import AsyncGenerator

from user_agents import user_agents
import random


class ProxyManager:
    def __init__(self):
        self.user_agent: str = random.choice(user_agents)

    @staticmethod
    async def get_all_proxies() -> AsyncGenerator[str, None]:
        """
            The function that gets the proxy list from the proxy_urls.json file.
        :return: AsyncGenerator
        """
        try:
            async with aiofiles.open("proxy_urls.json", 'r', encoding='utf-8') as file:
                data = await file.read()
                for item in json.loads(data):
                    yield item
        except (json.decoder.JSONDecodeError, FileNotFoundError) as ex:
            ex: str = "File proxy_urls.json has not been created" if isinstance(ex, FileNotFoundError) else "File proxy_urls.json is empty"
            logger.warning(ex)
            yield []

    async def get_proxy_for_request(self) -> AsyncGenerator[dict, None]:
        """
            The function that formats the proxy for the request.
        :return: AsyncGenerator
        """
        _data = {'server': '', 'username': '', 'password': ''}
        async for pr in self.get_all_proxies():
            if pr:
                _data['username'], _data['password'] = re.search(r'@(.*):(.*)', pr).groups()
                pr = pr.split("@")
                _data['server'] = f'http://{pr[-1]}@{pr[0]}'
                yield _data


if __name__ == '__main__':

    import asyncio
    async def main():
        per = ProxyManager()
        async for item in per.get_proxy_for_request():
            print(item)
            await asyncio.sleep(1)

    asyncio.run(main())