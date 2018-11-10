import requests
from bs4 import BeautifulSoup as bs
import re
import json
import os
from datetime import datetime
from settings import DATA_URL, RUN_AT
from threading import Thread
import schedule
from multiprocessing import Process
import time
import math


class SlowScraper:
    INIT_URL = 'https://27.ua/ua/shop/keramicheskaya-plitka-i-keramogranit/fs/otdelochnaya-poverhnost-stena/'
    WIDTH_HEIGHT_RE = re.compile(r'(?P<height>\d+,*?\d*?)[\*xх]+(?P<width>\d+,*?\d*?)')
    BASE_URL_TMPL = 'https://27.ua{}'
    continue_ = True

    def __init__(self, file_path, done_callback=None):
        self.file_path = file_path
        self.data = {'timestamp': None,
                     'items': []}
        self.done_callback = done_callback

    @classmethod
    def get_scraper(cls, done_callback=None):
        scraper = cls(done_callback=done_callback)

    def start_requests(self):
        next_link = self.parse(self.INIT_URL)
        while self.continue_:
            print(f'Parsed {next_link}')
            next_link = self.parse(next_link)
            if not next_link:
                self.continue_ = False
        self.save()
        if self.done_callback:
            self.done_callback()

    def parse(self, link):
        content = requests.get(link).content
        soup = bs(content, 'html.parser')
        next_link = soup.find('a', rel='next')['href']
        next_link = self.BASE_URL_TMPL.format(next_link)
        links = soup.select('a.custom-link.custom-link--big.custom-link--inverted.custom-link--blue')
        for item in links:
            name = item.b.string.strip()
            link = item['href']
            match = re.search(self.WIDTH_HEIGHT_RE, name)
            if match:
                width = match.group('width')
                height = match.group('height')
                height = float(height.replace(',', '.')) * 10 if height else None
                width = float(width.replace(',', '.')) * 10 if width else None
                url = self.BASE_URL_TMPL.format(link)
                tile = {'name': name, 'url': url,
                        'height': height, 'width': width}
                self.data['items'].append(tile)
        return next_link

    def save(self):
        with open(self.file_path, 'w', encoding='UTF-8') as fd:
            self.data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fd.write(json.dumps(self.data, ensure_ascii=False))


class Scheduler(Thread):
    def __init__(self, func_to_call):
        super().__init__(name="schedule_thread")
        schedule.every().day.at(RUN_AT).do(func_to_call)
        self.continue_ = True

    def run(self):
        while self.continue_:
            schedule.run_pending()
            time.sleep(3)
        print('Shedule thread finished')

    def terminate(self):
        self.continue_ = False


class Calc:
    __manager = None

    def __init__(self):
        self.reload()

    def reload(self):
        with open(DATA_URL) as fd:
                self.__data = json.loads(fd.read())['items']
        print('Data reloaded')

    def calc(self, height=None, width=None):
        result = []
        wh = float(height) * 1000.0
        ww = float(width) * 1000.0
        m2 = 1000 * 1000  # метр квадратний
        for item in self.__data:
            th = item['height']
            tw = item['width']
            # визначаємо кількість плиток по висоті та ширені
            dh = math.ceil(wh / th)
            dw = math.ceil(ww / tw)
            # площа плитки для стіни
            ta = (dh * dw) * (th * tw)
            ad = ta - wh * ww
            result.append({'area_diff_m': ad/m2,
                           'tile_count': dh * dw,
                           'tile_area_m': ta/m2,
                           'wall_area_m': (wh*ww)/m2,
                           'tile': item})
            result.sort(key=lambda x: x['area_diff_m'])
        return result[:3]


class ScraperProcessRunner:
    def __init__(self, done_callback):
        self.done_callback = done_callback
   
    def get_proc_func(self):
        scraper = SlowScraper(DATA_URL, self.done_callback)
        process = Process(target=scraper.start_requests, 
                          name='scraper_process')
        process.start()


def get_calc():
    calculator = Calc()
    proc_runnner = ScraperProcessRunner(calculator.reload)
    scheduler = Scheduler(proc_runnner.get_proc_func)
    scheduler.start()
    return calculator
