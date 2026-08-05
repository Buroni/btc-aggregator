# btc-aggregator

Builds a per-block Bitcoin dataset by combining Google BigQuery's public Bitcoin
dataset with detail scraped from blockchain.com.

For every calendar day the pipeline picks two blocks: the highest-total-output
block of the "dawn" half of the day (UTC hours 0–11) and the highest-total-output
block of the "dusk" half (UTC hours 12–23). Those blocks are then enriched with
the stats shown on the blockchain.com explorer page, plus the previous block hash
and merkle root from the blockchain.info API and a computed difficulty target.

## Data flow

```
BigQuery (bigquery-public-data.crypto_bitcoin)
  │  get_block_hashes.sql, run by query_block_hashes.py
  ▼
output/hash_query_out.csv          one row per selected block
  │  read by the "blockchain" Scrapy spider
  ▼
blockchain.com/explorer/blocks/btc/<hash>   (HTML scrape)
blockchain.info/block-height/<height>       (JSON API, per block)
  ▼
output/blockchain_out.csv          same rows + scraped/derived columns
```

Stage 1 is a single BigQuery job. Stage 2 is a Scrapy crawl that issues one
request per row of `hash_query_out.csv`, throttled to one concurrent request per
domain with a 3 second delay (see `btc_scrape/btc_scrape/settings.py`), so a full
run over the whole chain takes many hours.

## Prerequisites

- Python 3.10+
- A Google Cloud project with the BigQuery API enabled and a service account key
  with permission to run BigQuery jobs. The public Bitcoin dataset is readable by
  anyone, but query bytes are billed to your project — `get_block_hashes.sql`
  joins the full `blocks` and `transactions` tables with no date filter, so it
  scans a large amount of data. Check the dry-run cost before running it.
- Network access to `blockchain.com` and `blockchain.info` for stage 2.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Credentials

`query_block_hashes.py` authenticates through the standard
`GOOGLE_APPLICATION_CREDENTIALS` environment variable, which the BigQuery client
library reads on construction:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
```

If you do not export it, `query_block_hashes.py` falls back to
`google-api-creds.json` in the repository root, so the simplest setup is to drop
your service account key there — the file is listed in `.gitignore` and is never
committed. An exported value always takes precedence over the fallback.

To check what a run will cost before paying for it:

```bash
bq query --dry_run --use_legacy_sql=false < get_block_hashes.sql
```

## Usage

### Stage 1 — block hashes from BigQuery

Run from the repository root; the script resolves `get_block_hashes.sql` and the
`output/` directory relative to the current working directory, and `output/` must
already exist.

```bash
mkdir -p output
python3 query_block_hashes.py
```

Writes `output/hash_query_out.csv`, overwriting any previous run.

### Stage 2 — block detail from blockchain.com

```bash
cd btc_scrape
scrapy crawl blockchain
```

Writes to `output/blockchain_out.csv`. Some wrangling will need to be done in `blockchain.py` to resume from the last seen
hash if the scraper falls over.


## Project structure

```
.
├── get_block_hashes.sql        BigQuery SQL: picks the top-output block per day per dawn/dusk half
├── query_block_hashes.py       Runs the SQL and writes output/hash_query_out.csv
├── requirements.txt            Unpinned dependency list
├── google-api-creds.json       Service account key (gitignored, not in the repo)
├── output/                     Pipeline artifacts (gitignored)
└── btc_scrape/                 Scrapy project root — run scrapy from here
    ├── scrapy.cfg              Scrapy entrypoint config
    └── btc_scrape/
        ├── settings.py         Bot name, desktop user agent, robots.txt off, 1 req/domain, 3s delay
        ├── items.py            Unused Scrapy boilerplate (no ITEM_PIPELINES configured)
        ├── pipelines.py        Unused Scrapy boilerplate
        ├── middlewares.py      Unused Scrapy boilerplate
        └── spiders/
            ├── blockchain.py   The "blockchain" spider: requests each block page, parses it, appends CSV rows
            ├── data.py         CSS class names of the page, the scraped field list, CSV header, max target constant
            └── utils.py        blockchain.info lookup for prev block/merkle root; difficulty target maths
```

## Output files

### `output/hash_query_out.csv`

Header row written by `query_block_hashes.py`, one row per selected block,
ordered by timestamp ascending.

| Column | Description |
| --- | --- |
| `block_hash` | Block hash from `crypto_bitcoin.blocks` |
| `timestamp` | Block timestamp (UTC) |
| `date` | Date part of the timestamp |
| `year` | Year part of the timestamp |
| `month` | Month part of the timestamp |
| `day` | Day-of-month part of the timestamp |
| `time` | Time part of the timestamp |
| `time_of_day` | `dawn` for UTC hours 0–11, `dusk` for 12–23 |
| `output_value` | Sum of `transactions.output_value` for the block, in satoshis |

Only the block with the highest `output_value` within each (`date`,
`time_of_day`) group is kept.

### `btc_scrape/blockchain_out.csv`

Written by the spider, no header row. Columns, in order (names come from
`csv_header` in `spiders/data.py`):

| Column | Source |
| --- | --- |
| `block_hash`, `timestamp`, `date`, `year`, `month`, `day`, `time`, `time_of_day` | Copied through from `hash_query_out.csv` (`output_value` is not carried over) |
| `capacity`, `btc`, `value`, `average_value`, `median_value`, `transactions`, `minted`, `fees`, `average_fee`, `median_fee`, `confirmations`, `height`, `nonce`, `difficulty`, `bits`, `depth`, `size`, `weight`, `reward` | Scraped from the blockchain.com block page. Each is stripped of everything except digits and `.` and parsed as a float, so units, thousands separators and currency symbols are dropped |
| `version` | Scraped from the same page but kept as the raw string (e.g. `0x1`) |
| `previous_block_hash`, `merkle_root` | `prev_block` and `mrkl_root` from `https://blockchain.info/block-height/<height>?format=json`, taking the main-chain block |
| `difficulty_target` | `0x00000000FFFF0000…0000 // difficulty`, i.e. the max target divided by the scraped difficulty |
