import os
from pathlib import Path

from PIL import Image
from PyPDF2 import PdfReader, PdfWriter


class ImageToPDF:

    def __init__(self, name_gost: str):
        self.name_gost = name_gost
        self.list_images = []

    def run(self):

        # Define count pages
        self._define_count_page()

        # Create pdf from all png
        self._convert_png_to_pdf()

        # Read final pdf
        self._read_final_pdf()

        # Try to compress file
        self._compress_pdf()

        # Split large file
        if self._define_size_file(self.name_gost) > 50:
            self._split_pdf()

    def _define_count_page(self) -> None:
        """By count png in folder"""
        folder = Path(self.name_gost)
        self.count_pages = sum(1 for x in folder.iterdir())

    def _convert_png_to_pdf(self) -> None:
        """Convert all png to one pdf"""

        im = Image.open(f'{self.name_gost}/0.png')
        im_1 = im.convert('RGB')
        for i in range(1, self.count_pages):
            image = Image.open(f"{self.name_gost}/{i}.png")
            self.list_images.append(image.convert('RGB'))
        im_1.save(f'{self.name_gost}.pdf', save_all=True, append_images=self.list_images)

    def _read_final_pdf(self) -> None:
        self.reader = PdfReader(f'{self.name_gost}.pdf')

    def _compress_pdf(self) -> None:

        writer = PdfWriter()

        for page in self.reader.pages:
            page.compress_content_streams()
            writer.add_page(page)

        with open(f'{self.name_gost}.pdf', "wb") as f:
            writer.write(f)

    @staticmethod
    def _define_size_file(link: str) -> float:
        """Result in Mb"""
        return os.path.getsize(f'{link}.pdf') / 8 / 100000

    def _split_pdf(self):

        def _save_part_of_pdf(reader: PdfReader, pages: list, name_file: str, iterations: int):
            output = PdfWriter()
            for page in range(*pages):
                output.add_page(reader.pages[page])
            with open(f'{name_file}_{iterations}.pdf', "wb") as outputStream:
                output.write(outputStream)

        middle_page = self.count_pages // 2

        range_pages = {
            'first_half': [0, middle_page],
            'second_half': [middle_page + 1, self.count_pages + 1]
        }

        for i, half in enumerate(range_pages):
            _save_part_of_pdf(self.reader, range_pages[half], self.name_gost, i)
