import scrapy

class RedditSpider(scrapy.Spider):
    name = 'reddit'
    seen_titles = set()

    def __init__(self, keyword=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not keyword:
            raise ValueError("No keyword provided. You must use the -a flag with a keyword, e.g., -a keyword=hack")
        self.keyword = keyword

    def start_requests(self):
        target_url = f'https://old.reddit.com/search/?q={self.keyword}&sort=new&restrict_sr=&t=month'
        yield scrapy.Request(target_url, callback=self.parse)

    def parse(self, response):
        for link in response.css('div.search-result-group a::attr(href)'):
            href = response.urljoin(link.get())
            if 'comment' in href and href.startswith('https://old.reddit.com/r/'):
                yield scrapy.Request(href, callback=self.parse_post)

    def parse_post(self, response):
        try:
            title = response.css('a.title.may-blank::text').get()

            if title and title.lower() not in self.seen_titles:
                self.seen_titles.add(title.lower())
                content = response.css('div.expando div.md p::text').extract()

                yield {
                    'title': title.strip() if title else None,
                    'content': ' '.join(content).strip() if content else None
                }
        except Exception as e:
            self.log(f"Error processing post {response.url}: {str(e)}")