import requests
from .data import max_target

def get_prev_block_and_mrkl_root(height):
  height = int(height)
  url = f"https://blockchain.info/block-height/{height}?format=json"
  r = requests.get(url)
  json = r.json()

  block = next((x for x in json["blocks"] if x["main_chain"] == True))
  return [block["prev_block"], block["mrkl_root"]]

def get_difficulty_target(difficulty):
  return max_target // difficulty

def human_row_to_csv(human_row):
  return human_row.lower().replace(' ', '_')
