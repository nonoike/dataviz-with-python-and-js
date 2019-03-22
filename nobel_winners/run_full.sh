#!/bin/sh

pip install scrapy
pip install requests_cache

rm -f output/nwinners_full.json
scrapy crawl nwinners_full -o output/nwinners_full.json
