from influx_line_protocol import Metric, MetricCollection

collection = MetricCollection()
metric = Metric("weather")
metric.with_timestamp(1465839830100400200)
metric.add_tag('location', 'Cracow')
metric.add_tag('building', 'Central')
metric.add_value('temperature', '29')
collection.append(metric)

metric = Metric("weather")
metric.with_timestamp(1465839830100400200)
metric.add_tag('location', 'Nowy Sacz')
metric.add_value('temperature', '31')
collection.append(metric)

print(collection)
"""
  Will print
  weather,location="Cracow" temperature=29 1465839830100400200
  weather,location="Nowy Sacz" temperature=29 1465839830100400200
"""
