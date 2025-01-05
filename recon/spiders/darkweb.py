import scrapy
from requests_tor import RequestsTor
from scrapy.selector import Selector

class DarkwebSpider(scrapy.Spider):
    name = "darkweb"
    seen_titles = set()

    def __init__(self, keyword=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not keyword:
            raise ValueError("No keyword provided. You must use the -a flag with a keyword, e.g., -a keyword=hack")
        self.keyword = keyword

        self.tor_session = RequestsTor(tor_ports=(9050,), tor_cport=9051)

    def start_requests(self):
        check_tor_url = f'https://check.torproject.org'
        yield scrapy.Request(check_tor_url, callback=self.parse)

    def parse(self, response):
        base_url = 'http://bestteermb42clir6ux7xm76d4jjodh3fpahjqgbddbmfrgp4skg2wqd.onion/'
        target_url = base_url + f'search.php?keywords={self.keyword}'
        tor_response = self.tor_session.get(target_url)
        
        if tor_response.ok:
            selector = Selector(text=tor_response.text)
            hrefs = selector.css('div.postbody h3 a::attr(href)').extract()
            links = [base_url + href.lstrip('./') for href in hrefs]

            for link in links:
                try:
                    tor_response_post = self.tor_session.get(link)
                    
                    if tor_response_post.ok:
                        selector = Selector(text=tor_response_post.text)
                        title = selector.css('h2.topic-title a::text').get()

                        if title and title.lower() not in self.seen_titles:
                            self.seen_titles.add(title.lower())
                            content = selector.css('div.content::text').extract()
                            
                            yield {
                                'title': title if title else None,
                                'content': content if content else None,
                            }
                    else:
                        self.log(f"Failed to fetch content for link: {link} with status {tor_response_post.status_code}")
                
                except Exception as e:
                    self.log(f"Error while processing link {link}: {str(e)}")
                    continue
        else:
            self.log(f"Failed to fetch: {self.url} with status {tor_response.status_code}")