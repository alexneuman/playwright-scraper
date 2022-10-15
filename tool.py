import re
import csv
import os
from queue import Queue
from multiprocessing import Process, Array, Pool
from threading import Thread, Lock, Semaphore, BoundedSemaphore
from time import sleep
from typing import NamedTuple
from random import choice

from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from playwright_stealth import stealth_sync
from rich import print


from settings import BROWSER, USER_AGENTS, CONCURRENCY, RETRIES, HEADLESS
from inputs.inputs import previous_urls, set_inputs
from utils.misc import suppress
from utils.pia import change_region


class Settings:
    def _get_browser(self, playwright, random=False):
        browser = BROWSER.lower()
        if random:
            browser = choice(['chromium', 'firefox', 'webkit'])
        if browser == 'chromium':
            return playwright.chromium
        elif browser == 'firefox':
            return playwright.firefox
        elif browser == 'webkit':
            return playwright.webkit
        else:
            return playwright.chromium


RESULTS = []
DUPE_RESULTS = True
DUPE_PREV = True
DUPE_RESULTS_COL = 'url'
dupe_filter = previous_urls if DUPE_PREV else set()

sem = Semaphore(CONCURRENCY)

class Q(Queue):
    pass

class Manager:
    RETRIES = 20
    RETRIES_TO_BROWSER_CLOSE = 1
    queue = Q()
    lock = Lock()
    COUNTER = 0

    def __init__(self, inputs: list[str]|list[dict]|str, url_col: str, allowed_status_codes: list[int]|None = None, disallowed_status_codes: list[int]|None = None) -> None:
        i = set_inputs(inputs, url_col)
        print(i)
        self._url_col = url_col
        for row in i:
            url = getattr(row, url_col)
            if DUPE_RESULTS and url in dupe_filter:
                continue
            print('adding to queue')
            self.queue.put(row)
        
        if allowed_status_codes is None:
            self.allowed_status_codes = list(range(200, 300))
        if disallowed_status_codes is None:
            self.disallowed_status_codes = list(range(400, 600))
  

    def main(self, callback, row: tuple, page=None ,*args, **kwargs):
        try:
            # if not page:
            #     sem.acquire()
            # print("STARTING MAIN", row, page)
            # url = getattr(row, self._url_col)
            if not page:
                sem.acquire()
                url = getattr(row, self._url_col)
                print('ASSIGNING PAGE')
                page = self.get_page()
                page.row = row
                page._url = url
                page._callback = callback
            if page.RETRIES_TO_BROWSER_CLOSE <= 0:
                raise Exception('browser closed')
            print('ROW', row)
            page.goto(url, wait_until='domcontentloaded')
            # result = callback(page)
            results = callback(page)
            try:
                while (result := next(results)):
                    print('GOT SOME RESULT', result)
                    if result is None or not result:
                        print('RESULT IS NONE')
                        page.results = []
                        page.RETRIES_TO_BROWSER_CLOSE -= 1
                        self.main(callback, row, page, *args, **kwargs)
                    elif isinstance(result, Deferred):
                        print('RESULT IS DEFERRED')
                        self.queue.put(row)
                        page.results = []
                        # sem.release()
                        break
                    else:
                        print('RESULT IS NOT NONE')
                        page.results.append(result)
                        
            except StopIteration:
                pass
            # if isinstance(result, list):
            #     print('RESULT IS A LIST')
            #     page.results = result
            # else:
            #     print('RESULT IS NOT A LIST')
            #     page.results = [result]
            # print('added results!')
            # print(page.results)
            # page.close()
            # print('page closed!')
            # sem.release()
        except:
            self.queue.put(row)
            page.results = []
        finally:
            self.__class__.COUNTER += 1
            print(self.__class__.COUNTER, 'COUNTER')
            if self.__class__.COUNTER % 100000 == 0:
                print('VPN CHANGING!')
                with self.lock:
                    change_region(prefix='us')
                    sleep(600)
            with suppress():
                page.close()
            print(self.queue.qsize())
            sem.release()

    def start(self, callback, *args, **kwargs) -> None:
        while self.queue.qsize() > 0:
            threads = []
            print("STARTING")
            print("q is", self.queue.qsize())
            # while (inputs := self.queue.get()) is not None and len(threads) < CONCURRENCY:
            while len(threads) < CONCURRENCY:
                inputs = self.queue.get()
                t = Thread(target=self.main, args=(callback, inputs, args, kwargs))
                threads.append(t)
                print("appeded thread")
                t.start()
            for t in threads:
                t.join()
                # sleep(0.5)
            # if len(threads) >= CONCURRENCY:
            #     for t in threads:
            #         print("joining thread")
            #         print(len(threads))
            #         t.join()
            #         print('joined thread')
        print("FINISHED")

    def _next_url(self):
        return self.queue.get() or None

    def get_page(self):
        page = Page()
        page._set_manager(self)
        return page

class Deferred:
    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        
class SelectorsList(list):
    
    def __init__(self, page, selectors):
        self.selectors = []
        count = selectors.count()
        for i in range(count):
            locator = selectors.nth(i)
            self.append(Selector(page, locator))
        # self.selectors = [Selector(page, s) for s in selectors]
        # self.append(Selector(page, s) for s in selectors)
        
    # set iter to loop over selectors
    
    # def __iter__(self):
    #     iter(self.selectors)

    # def __get_item__(self, index):
    #     return self.selectors[index]
        
    def __repr__(self):
        return f'{self.selectors}'
    
        
class Selector():
    
    def __init__(self, page = None, _locator = None):
        self.page = page
        self.locator = _locator
        
    def _selector(
        self,
        selector: str,
        timeout: float = 1000,
        optional: bool = False,
        all: bool = False,
        page = None
    ):
        """
        Gets the xpath of the selector and returns the playwright selector object.
        Meant to alias the playwright selector object.
        """
        page = page or self.page
        if page is None:
            raise Exception("No page provided")
        
        with suppress(optional=optional):
            print("LOOKING FOR SELECTOR", selector)
            try:
                page.wait_for_selector(selector, timeout=timeout, state='attached')
            except:
                if page.RETRIES > 0:
                    page.RETRIES -= 1
                    print('RETRYING')
                    page.goto(page.url, wait_until='domcontentloaded')
                else:
                    pass
            
            if all:
                # return SelectorsList(selectors=page.query_selector_all(selector), page=page)
                return SelectorsList(selectors=page.locator(selector), page=page)
                
            else:
                # self.selector = page.query_selector(selector)
                if self.locator:
                    self.selector = self.locator.first.locator(selector).first
                else:
                    self.selector = page.locator(selector).first
                return self
        
    def xpath(self, selector: str, timeout: float = 1000, optional: bool = False, all: bool = False):
        if all:
            # create a new selector object
            return self.__class__(self.page)._selector(selector, timeout, optional, all)
        else:
            return self._selector(selector, timeout, optional, all)
        
    def text(self):
        return self.selector.first.inner_text()
    
    def get_attribute(self, attribute: str):
        return self.selector.get_attribute(attribute)
        

class Page:
    
    def __init__(self):
        playwright = sync_playwright().start()
        self.settings = Settings()
        self.browser = self.settings._get_browser(playwright, random=False).launch(headless=HEADLESS)
        self.context = self.browser.new_context(user_agent=choice(USER_AGENTS))
        self.page = self.context.new_page()
        stealth_sync(self.page)
        self.results = []
        self.OUTPUT_FILE = "results.csv"
        self.row: NamedTuple | None = None
        
        self.RETRIES = 10
        self.RETRIES_TO_BROWSER_CLOSE = 10
        self.total_request_count = 0
        
        self._url =  None
        self._callback = None

    def xpath(
        self,
        selector: str,
        attribute: str = "text_content",
        timeout: float = 1000,
        optional: bool = False,
        all: bool = False,
        delimiter: str = "\n",
    ):
        s = Selector(self).xpath(selector, timeout, optional, all)
        return s
        
        # with suppress(optional=optional):
        #     print("LOOKING FOR SELECTOR", selector)
        #     try:
        #         t = self.page.wait_for_selector(selector, timeout=timeout, state='attached')
        #     except:
        #         if self.RETRIES > 0:
        #             self.RETRIES -= 1
        #             print('RETRYING')
        #             self.goto(self.url, wait_until='domcontentloaded')
        #         else:
        #             print('PASSING')
        #             pass
        #             # self.close()
        #             # return self.deferred(self.xpath, selector, attribute, timeout, optional, all, delimiter)
            
        #     if all:
        #         r = self.page.query_selector_all(selector)
        #         if attribute == "text_content":
        #             return [r.inner_text() for r in r]
        #         elif attribute:
        #             return [r.get_attribute(attribute) or "" for r in r]

        #     if attribute == "text_content":
        #         r = self.page.query_selector(selector)
        #         print('got r', r.inner_text())
        #         return r.inner_text() if r else ""
        #     r = self.page.query_selector(selector)
        #     print('attribute is', attribute)
        #     return r.get_attribute(attribute) if r else ""

    def goto(
        self,
        url: str,
        ignore_errors: bool = False,
        retries: int = RETRIES,
        delay: int = 10000,
        *args,
        **kwargs,
    ):
        if self.RETRIES_TO_BROWSER_CLOSE <= 0:
            print('NO MORE RETRIES! CLOSING')
            self.close()
        if url in dupe_filter:
            return
        print("GOING TO URL")
        self.page.wait_for_timeout(delay)
        resp = self.page.goto(url, *args, **kwargs)
        
        print('RESP', resp)
        if resp is not None and resp != () and resp.status in self.manager.allowed_status_codes and resp.status not in self.manager.disallowed_status_codes:
            print('GOOD RESPONSE', resp.status)
            # dupe_filter.add(url)
            return
        else:
            # bad response
            print('BAD RESPONSE')
            self.wait_for_timeout(delay)
            self.RETRIES_TO_BROWSER_CLOSE -= 1
            try:
                self.results = []
                self.goto(url, delay=delay)
                print('WENT TO URL')
            except:
                # self.close()
                # self.manager.queue.put(self.row)
                raise ValueError('BAD RESPONSE')
                print('THE BROWSER WAS FORCEFULLY CLOSED', self.url.replace('https://', ''))
            finally:
                pass
                # sem.release()
                
    def click_gone(self, selector, timeout=1000, delay=100, optional=False, *args, **kwargs):
        with suppress(optional=optional):
            try:
                self.page.wait_for_selector(selector, timeout=timeout, state='attached')
                while True:
                    elements = self.page.query_selector_all(selector)
                    for element in elements:
                        element.click()
                        self.page.wait_for_timeout(delay)
                    if self.page.wait_for_selector(selector, timeout=0, state='attached') is None:
                        break
            except:
                self.browser.close()
            

    def close(self):
        print('closing page')
        self._write_output(items=self.results, output_file=self.OUTPUT_FILE)
        if self.results:
            print('THERE aRe RESULTS')
        else:
            print('NO RESULTS')
        self.browser.close()
        dupe_filter.add(self.url)
        print('closed browser!')
        
    def scroll(self, selector, timeout=1000, delay=100, optional=False, *args, **kwargs):
        with suppress(optional=optional):
            try:
                self.page.wait_for_selector(selector, timeout=timeout, state='attached')
                ele = self.page.query_selector(selector)
                ele.scroll_into_view()
            except:
                self.close()

    def _get_next_url(self):
        self.current_url = self.manager._next_url()
        return self.current_url

    def _write_output(
        self, items, output_file: str = None, fieldnames: list[str] = None
    ):
        if items:
            if not os.path.exists(output_file or self.OUTPUT_FILE):
                with open(self.OUTPUT_FILE, "w") as f:
                    writer = csv.DictWriter(
                        f, fieldnames=fieldnames or self.results[0].keys()
                    )
                    writer.writeheader()
            with open(self.OUTPUT_FILE, "a") as f:
                writer = csv.DictWriter(
                    f, fieldnames=fieldnames or self.results[0].keys()
                )
                for r in items:
                    writer.writerow(r)
                    del r
                    
    def deferred(self, callback, *args, **kwargs):
        return Deferred(callback, *args, **kwargs)

    def _set_manager(self, manager):
        self.manager = manager

    def __getattr__(self, att):
        return getattr(self.page, att)

    def __getattribute__(self, att: str):
        if getattr(super(), "__getattribute__"):
            return super().__getattribute__(att)
        return getattr(self.page, att)
