import re
import requests
import scrapy
from nobel_winners.items import NWinnersItem

# scrapy crawl nwinners_full


class NWinnerFullSpider(scrapy.Spider):
    """ 受賞者の国とリンクテキストをスクレイピングする """
    name = 'nwinners_full'  # scrapyコマンドで呼び出される名前
    allowed_domains = ['en.wikipedia.org', 'wikidata.org']  # クロールするドメイン
    start_urls = [  # ダウンロードされる最初のページ
        'https://en.wikipedia.org/wiki/List_of_Nobel_laureates_by_country'
    ]

    def parse(self, response):
        # print(response) # Ex. <200 https://en.wikipedia.org/wiki/List_of_Nobel_laureates_by_country>

        # 要素に紐づく属性は@で表記
        h3s = response.xpath('//*[@id="mw-content-text"]/div/h3')

        for h3 in h3s:
            # xpath('${hoge_xpath}/text()').extract() でテキストを取得
            country = h3.xpath('span[@class="mw-headline"]/text()').extract()

            if country:
                # following-sibling:: で次の要素を取得
                winners = h3.xpath('following-sibling::ol[1]')

                for w in winners.xpath('li'):
                    wdata = self.process_winner_li(w, country[0])
                    request = scrapy.Request(
                        wdata['link'], callback=self.parse_bio, dont_filter=True)
                    request.meta['item'] = NWinnersItem(**wdata)
                    yield request
            break # TODO: 動作確認用に途中でストップさせている → 確認後に行削除

    def process_winner_li(self, w, country=None):
        """ 受賞者の <li> タグを処理し、該当する場合は出生国か国籍を追加する。 """
        text = ' '.join(w.xpath('descendant-or-self::text()') .extract())
        # print(text) # Ex. ['Tawakkol Karman', ', Peace, 2011']

        wdata = {}
        wdata['link'] = 'https://en.wikipedia.org' + \
            w.xpath('a/@href').extract()[0]
        wdata['name'] = text.split(',')[0].strip()
        year = re.findall('\d{4}', text)
        wdata['year'] = int(year[0]) if(year) else 0
        category = re.findall(
            'Physics|Chemistry|Physiology or Medicine|Literature|Peace|Economics', text)
        wdata['category'] = category[0] if(category) else ''
        # 受賞者の後のアスタリスクは、受賞時の国が受賞者の出生国(国籍ではない)であることを示す
        if country:
            if text.find('*') != -1:
                wdata['country'] = ''
                wdata['born_in'] = country
            else:
                wdata['country'] = country
                wdata['born_in'] = ''
        wdata['text'] = text
        return wdata

    def parse_bio(self, response):
        """ 受賞者の紹介をスクレイピングする。 """
        # print(response) # Ex. <200 https://en.wikipedia.org/wiki/C%C3%A9sar_Milstein>
        item = response.meta['item']
        href = response.xpath('//*[@id="t-wikibase"]/a/@href').extract()
        # print(href) # Ex. ['https://www.wikidata.org/wiki/Special:EntityPage/Q155525']

        if href:
            wikidata_title_id = href[0].split('/')[-1]
            property_codes = [
                {'name': 'date_of_birth', 'code': 'P569',
                    'value_element_name': 'time'},
                {'name': 'date_of_death', 'code': 'P570',
                    'value_element_name': 'time'},
                {'name': 'place_of_birth', 'code': 'P19',
                    'value_element_name': 'id', 'is_link': True},
                {'name': 'place_of_death', 'code': 'P20',
                    'value_element_name': 'id', 'is_link': True},
                {'name': 'gender', 'code': 'P21',
                    'value_element_name': 'id', 'is_link': True}
            ]
            for prop in property_codes:
                # スクレイピングでは `Forbidden by robots.txt` になるためリクエストを投げてパースする
                item[prop['name']] = self.fetch_person_data(
                    wikidata_title_id, prop['code'], prop['value_element_name'], prop.get('is_link', False))

        yield item

    def fetch_wikidata(self, wikidata_title_id):
        """ wikidata の json レスポンスを取得する。 """
        url = 'https://www.wikidata.org/entity/{wikidata_title_id}'.format(
            wikidata_title_id=wikidata_title_id)
        res = requests.get(url)
        return res.json()

    def fetch_person_data(self, wikidata_title_id, claims_id, value_element_name, is_link):
        """ 人物情報を取得する。・ """
        try:  # TODO: データ取得箇所が適切か要検討
            json = self.fetch_wikidata(wikidata_title_id)
            value = json['entities'][wikidata_title_id]['claims'][claims_id][0]['mainsnak']['datavalue']['value'][value_element_name]
            if is_link:
                json = self.fetch_wikidata(value)
                value = json['entities'][value]['labels']['en']['value']
            return value
        except Exception as e:  # データ無しでも構わないのでエラーハンドリングは妥協する
            print('not exists {}'.format(e))
            return ''
