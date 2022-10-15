
import re

def google(page):
    page.wait_for_timeout(500)
    results = page.xpath('//h3/ancestor::node()[3]', all=True)
    print(results, 'RESULTS', type(results))
    page.wait_for_timeout(2000)
    
    for result in results:
        # url =  result.selector.first.locator('//a').first.get_attribute('href')
        url = result.xpath('//a').get_attribute('href')
        url = re.match(r'https[^&]+', url).group(0)
        # url = re.match(r'https[^&]+', url).group(0)
        page.wait_for_timeout(500)
        yield {'url': url, 'starting_url': page.row.url}