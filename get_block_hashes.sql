with block_values as (
  select
    b.hash as block_hash,
    b.timestamp as timestamp,
    extract(date from b.timestamp) as date,
    extract(year from b.timestamp) as year,
    extract(month from b.timestamp) as month,
    extract(day from b.timestamp) as day,
    extract(time from b.timestamp) as time,
    sum(t.output_value) as output_value,
    if(
        extract(hour from timestamp) between 0 and 11,
        'dawn',
        'dusk'
      ) as time_of_day
  from
    `bigquery-public-data.crypto_bitcoin.blocks` as b
  join
    `bigquery-public-data.crypto_bitcoin.transactions` as t
  on b.hash = t.block_hash
  group by b.hash, b.timestamp
  order by b.timestamp asc
),
row_numbers as (
  select
    bv.block_hash as block_hash,
    bv.timestamp as timestamp,
    bv.date as date,
    bv.year as year,
    bv.month as month,
    bv.day as day,
    bv.time as time,
    bv.time_of_day as time_of_day,
    bv.output_value as output_value,
    row_number() over (partition by bv.date, bv.time_of_day order by bv.output_value desc) as value_rn
  from
    block_values as bv
)
select
  rn.block_hash as block_hash,
  rn.timestamp as timestamp,
  rn.date as date,
  rn.year as year,
  rn.month as month,
  rn.day as day,
  rn.time as time,
  rn.time_of_day as time_of_day,
  rn.output_value as output_value
from
  row_numbers as rn
where
  rn.value_rn = 1
order by
  timestamp asc;
