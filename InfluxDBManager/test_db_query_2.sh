curl -G 'http://172.104.55.158:8086/query?pretty=true' --data-urlencode "db=ticks" --data-urlencode "q=SELECT mean(\"ltp\")" FROM \"FeedFull\""

SELECT mean("ltp"), mean("ltp") FROM "FeedFull" WHERE $timeFilter GROUP BY time(10s) fill(null)
