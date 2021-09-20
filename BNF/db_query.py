from influxdb import InfluxDBClient
import pandas as pd

def main(host='localhost', port=8086):
    """Instantiate a connection to the InfluxDB."""
    # query = 'select Float_value from cpu_load_short;'
    # query_where = 'select Int_value from cpu_load_short where host=$host;'
    # query = 'SELECT last("ltp") FROM "FeedFull" WHERE time >= now() - 5m GROUP BY time(10s) fill(null)'
    query = 'SELECT difference(last("vtt")) AS "VolumeD", first("ltp") AS "Open", max("ltp") AS "High", min("ltp") AS "Low", last("ltp") AS "Close", last("asks_0_price") AS "Ask", last("bids_0_price") AS "Bid" FROM "FeedFull" WHERE time >= now() - 2m GROUP BY time(1m)'

    client = InfluxDBClient(host='localhost', port=8086, database='ticks')

    result = client.query(query)

    data = result.raw

    df = pd.DataFrame(data['series'][0]['values'])
    df.columns = data['series'][0]['columns']
    print(df)

if __name__ == '__main__':
    main()
