from telegraf.client import TelegrafClient
client = TelegrafClient(host='localhost', port=8092)

# Records a single value with no tags
client.metric('some_metric', 123)

# Records a three values with different data types
client.metric('some_metric', {'value_a': 100, 'value_b': 100, 'value_c': True})

# Records a single value with one tag
client.metric('some_metric', 123, tags={'server_name': 'my-server'})
