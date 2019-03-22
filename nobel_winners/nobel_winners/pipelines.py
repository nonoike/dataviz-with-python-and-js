# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import scrapy
from nobel_winners.items import NWinnersItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem


class DropNonPersons(object):
    def process_item(self, item, spider):
        """ 人物ではなく団体に贈られた賞を除外する。 """
        if not item['gender']:
            raise DropItem("No gender for %s" % item['name'])
        return item


class NobelImagesPipeline(ImagesPipeline):
    # ImagesPipeline で用意されているメソッド
    def get_media_requests(self, item, info):
        """ 画像URLへのリクエストを送信する。 """
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url)

    # ImagesPipeline で用意されているメソッド
    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if image_paths:
            item['bio_image'] = image_paths[0]
        return item
