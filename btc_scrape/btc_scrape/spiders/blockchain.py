import scrapy
from scrapy.selector import Selector
from .data import blockchain_com_cols, csv_header
from .utils import get_prev_block_and_mrkl_root, get_difficulty_target
import csv
import os
import re

OUTPUT_PATH = "../output/blockchain_out.csv"

VALUE_FOR_LABEL = (
    "//div[normalize-space(text())=$label]"
    "/ancestor::div[following-sibling::div][1]"
    "/following-sibling::div[1]"
)

def get_value_from_response(response, label):
    return response.xpath(VALUE_FOR_LABEL, label=label).xpath("normalize-space(.)").get()

class BlockchainSpider(scrapy.Spider):
    name = "blockchain"
    allowed_domains = ["blockchain.com"]

    async def start(self):
      self.maybe_write_header()

      with open("../output/hash_query_out.csv", newline="\n") as f_sql:
        sql_reader = csv.reader(f_sql, delimiter=',')
        next(sql_reader, None)

        for idx, row in enumerate(sql_reader):
          hash = row[0]
          timestamp = row[1]
          date = row[2]
          year = row[3]
          month = row[4]
          day = row[5]
          time = row[6]
          time_of_day = row[7]

          url = f"https://www.blockchain.com/explorer/blocks/btc/{hash}"
          yield scrapy.Request(
            url=url,
            callback=self.parse,
            meta=dict(
              idx=idx,
              hash=hash,
              timestamp=timestamp,
              date=date,
              year=year,
              month=month,
              day=day,
              time=time,
              time_of_day=time_of_day
            )
          )

    def parse(self, response):
      selector = Selector(text=response.body)
      meta = response.meta

      self.log_row(meta)

      with open(OUTPUT_PATH, "a", newline="\n") as f_write:
        writer = csv.writer(f_write, delimiter=",")

        row = [
          meta.get('hash'),
          meta.get('timestamp'),
          meta.get('date'),
          meta.get('year'),
          meta.get('month'),
          meta.get('day'),
          meta.get('time'),
          meta.get('time_of_day'),
        ]

        for col in blockchain_com_cols:
          try:
            raw_value = get_value_from_response(selector, col)
            value = self.format_value(raw_value, col)
            row.append(value)

            if col == 'Height':
              height = value
            elif col == 'Difficulty':
              difficulty = value
          except:
            self.log(f'Error parsing column {col}, value {raw_value}')
            raise

        prev_block_and_mrkl_root = get_prev_block_and_mrkl_root(height)
        row.extend(prev_block_and_mrkl_root)

        difficulty_target = get_difficulty_target(difficulty)
        row.append(difficulty_target)

        writer.writerow(row)

    def log_row(self, meta):
      hash = meta.get('hash')
      idx = meta.get('idx')
      self.log(f'Parsing block {hash}; row {idx}')

    def format_value(self, value, row):
      if row == "Version":
        return value
      return float(re.sub(r'[^0-9.]', '', value))

    def maybe_write_header(self):
      # parse() appends, so only write the header when starting a fresh file
      if os.path.exists(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 0:
        return

      with open(OUTPUT_PATH, "w", newline="\n") as f_write:
        csv.writer(f_write, delimiter=",").writerow(csv_header)
