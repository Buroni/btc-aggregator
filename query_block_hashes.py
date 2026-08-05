from google.cloud import bigquery
import csv
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google-api-creds.json"

OUT_PATH = 'output/hash_query_out.csv'

def get_query_job(client):
  with open('get_block_hashes.sql', 'r') as f_query:
    sql_query = f_query.read()
    query_job = client.query(sql_query)

  return query_job

def process_to_csv(query_job):
  with open(OUT_PATH, 'w', newline="\n") as f_write:
    writer = csv.writer(f_write, delimiter=',')
    writer.writerow([
      'block_hash',
      'timestamp',
      'date',
      'year',
      'month',
      'day',
      'time',
      'time_of_day',
      'output_value'
    ])

    for row in query_job.result():
      writer.writerow(row)


def main():
  print('🟡 Fetching block hashes')
  try:
    client = bigquery.Client()
    query_job = get_query_job(client)
    process_to_csv(query_job)
  except Exception as e:
    print('🔴 An error occurred: ', e)
    raise e
  print(f'🟢 Wrote result to {OUT_PATH}')

if __name__ == "__main__":
    main()
