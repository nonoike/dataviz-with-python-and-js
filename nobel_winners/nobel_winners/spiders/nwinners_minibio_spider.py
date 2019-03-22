import re
import scrapy
from nobel_winners.items import NWinnerItemBio

# scrapy crawl nwinners_minibio -o output/minibios.json

class NWinnerSpiderBio(scrapy.Spider):
    name = 'nwinners_minibio'
    allowed_domains = ['en.wikipedia.org']
    start_urls = [
        "https://en.wikipedia.org/wiki/List_of_Nobel_laureates_by_country"
    ]
    custom_settings = {
        'ITEM_PIPELINES': {'nobel_winners.pipelines.NobelImagesPipeline': 1},
        'IMAGES_STORE': 'output/images'
    }

    def parse(self, response):
        h3s = response.xpath('//*[@id="mw-content-text"]/div/h3')

        for h3 in h3s:
            country = h3.xpath('span[@class="mw-headline"]/text()').extract()

            if country:
                winners = h3.xpath('following-sibling::ol[1]')

                for w in winners.xpath('li'):
                    wdata = {}
                    wdata['link'] = 'https://en.wikipedia.org' + \
                        w.xpath('a/@href').extract()[0]
                    request = scrapy.Request(
                        wdata['link'], callback=self.get_mini_bio, dont_filter=True)
                    request.meta['item'] = NWinnerItemBio(**wdata)
                    yield request
            break  # 動作確認用に途中でストップ

    def get_mini_bio(self, response):
        """ 受賞者の人物情報テキストと写真を取得する。 """
        item = response.meta['item']
        item['image_urls'] = []
        img_src = response.xpath(
            '//table[contains(@class,"infobox")]//img/@src')
        if img_src:
            item['image_urls'] = ['https:' + img_src[0].extract()]
        item['mini_bio'] = self.create_mini_bio_item(response, item['link'])
        yield item

    def create_mini_bio_item(self, response, link):
        # TODO: 未完成なので修正する
        """ 人物情報を取得する。 """
        mini_bio = ''
        for text in response.xpath('//*[@id="mw-content-text"]/div/p[position() <= 2 and not(contains(@class, "mw-empty-elt"))]').extract():
            # ウィキリンクの補正
            print("==={}".format(text))
            mini_bio += text \
                .replace('href="/wiki', 'href="http://en.wikipedia.org/wiki') \
                .replace('href="#', link + '#')
        return mini_bio
