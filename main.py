
from time import sleep
import re

from rich import print

from tool import Manager, Deferred
from utils.url_helpers import google_decode, get_google_url

def linkedin(page):
    page.wait_for_timeout(200000)
    if 'auth' in page.url or 'wall' in page.url or page.url == 'about:blank':
        print('RETURNING NONE')
        return None
    else:
        print('SUCCESS', page.url)
        print('TRYING NEXT')
        # urls = page.xpath('//h3/../..//*[@href]', all=True, timeout=3000, attribute='href')
        bob = page.xpath('//bob', optional=True)
        name = page.xpath('//h1', optional=True)
        job_title = page.xpath('//h2[contains(@class, "leading-open") and not(contains(text(), " Activity "))]', optional=True)
        company = page.xpath('(//div[@class="profile-section-card__contents"]/..)//h4', optional=True)
        if not company:
            company = page.xpath('//section[@id="ember96"]//li//span[@class="mr1 t-bold"]', optional=True)
        time_with_company = page.xpath('//span[@class="date-range__duration"]', optional=True)
        connections = page.xpath('//span[contains(text(), "onnection")]', optional=True)
        leading_open = page.xpath('//h2[contains(@class, "leading-open")]', optional=True)
        location = page.xpath('//h3/span', optional=True)
        found_words = []
        useful_words = []
        bio = page.xpath('//h2[contains(text(), "About") and contains(@class, "core")]/following-sibling::*', optional=True)
        # print(urls, 'name')
        yield {'name': name, 'bio': bio, 'job_title': job_title,'starting_url': page.row.starting_url,
                'company': company, 'time_with_company': time_with_company, 'connections': connections, 'leading_open': leading_open,
                'location': location, 'key_words': ','.join(found_words)}
        
def google(page):
    page.wait_for_timeout(500)
    results = page.xpath('//h3/ancestor::node()[3]', all=True)
    page.wait_for_timeout(2000)
    
    for result in results:
        # url =  result.selector.first.locator('//a').first.get_attribute('href')
        url = result.xpath('//a[@href]').get_attribute('href')
        if '&' in url and url is not None:
            url = re.match(r'https[^&]+', url)
            if url:
                url = url.group(0)
            else:
                print('DEFERRING')
                return Deferred(callback=google)
        # url = re.match(r'https[^&]+', url).group(0)
        page.wait_for_timeout(200)
        yield {'url': url, 'starting_url': page.row.url}
        
def office_depot(page):
    page.wait_for_timeout(5000000)
    return

def hermes(page):
    print('HERMES', page.response)
    page.wait_for_timeout(50000)
    return {'bob': 1}

if __name__ == '__main__':
    # m = Manager([get_google_url(i + ' podcast', site='linkedin.com/in/', num_pages=100) for i in ('constitution', 'free market', 'libertarian', 'capitalist', 'constitution', 'liberty', 'local government')], url_col='url')
    m = Manager(inputs=['https://www.walmart.com/shop/Halloween-Candy' for _ in range(1)], url_col='url')
    m.start(callback=hermes)
