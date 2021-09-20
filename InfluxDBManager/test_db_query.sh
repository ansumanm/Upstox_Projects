curl -G 'http://172.104.55.158:8086/query?pretty=true' --data-urlencode "db=ticks" --data-urlencode "q=SELECT \"ltp\",\"symbol\" FROM \"FeedFull\""
