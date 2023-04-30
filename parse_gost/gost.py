import os
import shutil
import re
import logging
from typing import Tuple

import requests
from bs4 import BeautifulSoup

from parse_gost.png_to_pdf import ImageToPDF

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Gost:
    """
    Parsing GOST and other documentation from protect.gost.ru
    """

    BASE_URL = "https://protect.gost.ru"

    def __init__(self, gost_url: str, name_gost: str):
        self.session_id, self.gost_url = self._prepare_url(gost_url)
        self.headers = {'cookie': f'ASP.NET_SessionId={self.session_id}'}
        self.gost_soupy = self._get_soupy(gost_url, self.headers)
        self.name_gost = name_gost
        self.list_links_page = []
        self.list_links_image = []

        # Create folder for saving png
        os.mkdir(self.name_gost)

    def get(self) -> None:
        logger.info(f'start for url={self.gost_url}')
        # Collect all links to pages with list png
        self._get_all_links_page_gost()
        logger.info(f'get_all_links_page_gost >>> {len(self.list_links_page)}')

        # Collect all links to pages with png
        self._get_all_links_image()
        logger.info(f'get_all_links_image >>> {len(self.list_links_image)}')

        # Save links by loops
        for n, link_image in enumerate(self.list_links_image):
            self._get_and_save_image(n, link_image)
        logger.info(f'loop image >>> done')

        ImageToPDF(self.name_gost).run()

        # Clean up
        shutil.rmtree(self.name_gost)

    def _get_all_links_page_gost(self) -> None:
        """Collect all links to pages with list png"""
        for a in self.gost_soupy.find_all('a'):
            if a.getText().isnumeric():
                self.list_links_page.append(self.BASE_URL + a.get('href'))

    def _get_all_links_image(self) -> None:
        """Collect all links to pages with png"""
        for link in self.list_links_page:
            page_soupy = self._get_soupy(link, self.headers)
            self.list_links_image.append(self._get_image_link(page_soupy))

    def _get_and_save_image(self, n: int, link_image: str) -> None:
        """Get pic and save him"""
        img_data = requests.get(link_image, headers=self.headers).content
        with open(f"{self.name_gost}/{n}.png", 'wb') as handler:
            handler.write(img_data)

    def _get_image_link(self, image_page: BeautifulSoup) -> str:
        """Get link to png from css"""
        link_page = None
        for link in image_page.find_all('link'):
            link_page = link.get('href') if 'page' in link.get('href') else None
        css_style = requests.get(f'{self.BASE_URL}/{link_page}').text
        return self.BASE_URL + '/' + re.findall(r'\((.*?)\)', css_style)[0]

    def _prepare_url(self, gost_url: str) -> Tuple[str, str]:
        """Prepare url and get session id ASP.NET"""
        req = requests.get(gost_url)
        session_id = req.cookies.get_dict()['ASP.NET_SessionId']
        s = BeautifulSoup(req.content, 'html.parser')
        gost_url = [
            a.get('href') for a in s.find_all('a')
            if 'http' not in a.get('href')
            and a.find('img') is None
        ]
        full_gost_url = self.BASE_URL + '/' + gost_url[0]
        return session_id, full_gost_url

    @staticmethod
    def _get_soupy(gost_url: str, headers: dict) -> BeautifulSoup:
        """Get soupy from url"""
        html = requests.get(gost_url, headers=headers)
        return BeautifulSoup(html.content, 'html.parser')
