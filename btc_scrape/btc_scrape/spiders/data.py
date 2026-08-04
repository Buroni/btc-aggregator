# Class of the div encompassing each data row on the blockchain page.
# Note this may change if website is updated.
row_div_class = 'sc-9af3ec78-2 hYPCfn'

# Class of the div containing the value of the row
value_div_class = 'sc-3391354d-2 gOhep'

# Previous block hash for block 0 (no previous hash defaults to all zeroes)
default_prev_block_hash = '0000000000000000000000000000000000000000000000000000000000000000'

# Used to calculate difficulty target
max_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000

blockchain_com_cols = [
  'Capacity',
  'BTC',
  'Value',
  'Average Value',
  'Median Value',
  'Transactions',
  'Minted',
  'Fees',
  'Average Fee',
  'Median Fee',
  'Confirmations',
  'Height',
  'Nonce',
  'Difficulty',
  'Version',
  'Bits',
  'Depth',
  'Size',
  'Weight',
  'Reward',
]

csv_header = [
  'block_hash',
  'timestamp',
  'date',
  'year',
  'month',
  'day',
  'time',
  'time_of_day',
  'capacity',
  'btc',
  'value',
  'average_value',
  'median_value',
  'transactions',
  'minted',
  'fees',
  'average_fee',
  'median_fee',
  'confirmations',
  'height',
  'nonce',
  'difficulty',
  'version',
  'bits',
  'depth',
  'size',
  'weight',
  'reward',
  'previous_block_hash',
  'merkle_root',
  'difficulty_target',
]
