#!/bin/sh

pip install scrapy

rm -f output/minibios.json
scrapy crawl nwinners_minibio -o output/minibios.json
