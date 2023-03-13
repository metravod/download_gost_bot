import os
import shutil

from typing import Tuple
import re
import requests
from bs4 import BeautifulSoup
from PIL import Image
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


class Gost:
    """
    Класс для парсинга изображений со страницами ГОСТов с protect.gost.ru
    """

    BASE_URL = "https://protect.gost.ru"

    def __init__(self, gost_url: str, name_gost: str):
        self.session_id, self.gost_url = self._prepare_url(gost_url)
        self.headers = {'cookie': f'ASP.NET_SessionId={self.session_id}'}
        self.gost_soupy = self._get_soupy(gost_url, self.headers)
        self.name_gost = name_gost
        self.list_links_page = []
        self.list_links_image = []

        # Создаем папку для сохранения png
        os.mkdir(self.name_gost)

    def get(self) -> None:

        # Собираем все ссылки на страницы ГОСТа с png
        self._get_all_links_page_gost()
        logger.info(f'get_all_links_page_gost >>> {len(self.list_links_page)}')

        # Собираем все ссылки на сами png страниц ГОСТа
        self._get_all_links_image()
        logger.info(f'get_all_links_image >>> {len(self.list_links_image)}')

        # Идем по циклу по всем ссылкам на png и сохраняем их
        for n, link_image in enumerate(self.list_links_image):
            self._get_and_save_image(n, link_image)
        logger.info(f'loop image >>> done')

        # Преобразуем отдельные png в один целый pdf
        self._convert_png_to_pdf()
        logger.info(f'convert_png_to_pdf >>> done')

        # Подчищяем за собой папку с png
        shutil.rmtree(self.name_gost)

    def _get_all_links_page_gost(self) -> None:
        """Собираем все ссылки на страницы госта c png"""
        for a in self.gost_soupy.find_all('a'):
            if a.getText().isnumeric():
                self.list_links_page.append(self.BASE_URL + a.get('href'))

    def _get_all_links_image(self) -> None:
        """Собираем все ссылки на png со страницами госта"""
        for link in self.list_links_page:
            page_soupy = self._get_soupy(link, self.headers)
            self.list_links_image.append(self._get_image_link(page_soupy))

    def _get_and_save_image(self, n: int, link_image: str) -> None:
        """Забираем изображение и сохраняем его"""
        img_data = requests.get(link_image, headers=self.headers).content
        with open(f"{self.name_gost}/{n}.png", 'wb') as handler:
            handler.write(img_data)

    def _convert_png_to_pdf(self) -> None:
        """Преобразуем png в один целый pdf"""
        list_images = []
        im = Image.open(f'{self.name_gost}/0.png')
        im_1 = im.convert('RGB')
        for i in range(1, 11):
            image = Image.open(f"{self.name_gost}/{i}.png")
            list_images.append(image.convert('RGB'))
        im_1.save(f'{self.name_gost}.pdf', save_all=True, append_images=list_images)

    def _get_image_link(self, image_page: BeautifulSoup) -> str:
        """Получение ссылки на png из css стилей страницы госта"""
        for link in image_page.find_all('link'):
            link_page = link.get('href') if 'page' in link.get('href') else None
        css_style = requests.get(f'{self.BASE_URL}/{link_page}').text
        return self.BASE_URL + '/' + re.findall(r'\((.*?)\)', css_style)[0]

    def _prepare_url(self, gost_url: str) -> Tuple[str, str]:
        req = requests.get(gost_url)
        logger.info(f'start requests >>> {req}')
        session_id = req.cookies.get_dict()['ASP.NET_SessionId']
        logger.info(f'session_id >>> {session_id}')
        s = BeautifulSoup(req.content, 'lxml')
        logger.info(f"first soup >>> {s}")
        gost_url = [
            a.get('href') for a in s.find_all('a')
            if 'http' not in a.get('href')
            and a.find('img') is None
        ]
        logger.info(f'len gost_url >>> {len(gost_url)}')
        full_gost_url = self.BASE_URL + '/' + gost_url[0]
        return session_id, full_gost_url

    @staticmethod
    def _get_soupy(gost_url: str, headers: dict) -> BeautifulSoup:
        """Получем супчик из урла"""
        html = requests.get(gost_url, headers=headers)  # .text
        return BeautifulSoup(html.content, 'lxml')
