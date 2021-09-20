#!/usr/bin/env python3
import os
import sys
import atexit
import readline
from cmd2 import Cmd
from influxdb_client import Point, InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


history_file = os.path.expanduser('~/.IDB_Cloud_history')
if not os.path.exists(history_file):
    with open(history_file, "w") as fobj:
        fobj.write("")
readline.read_history_file(history_file)
atexit.register(readline.write_history_file, history_file)

class REPL(Cmd):
    prompt = "IDB> "
    intro = """
	InfluxDB Manager CLI 
    """

    def __init__(self):
        Cmd.__init__(self)
        self.influx_cloud_url = 'https://us-west-2-1.aws.cloud2.influxdata.com'
        self.influx_cloud_token = 'vxdOLg2pfVu1lBzo_kovCNPGlnBeN8NsYa6XJYYOfa3vrjZ4lRsxuwI3uCAZSfm9In102YzZYe-KlrFeK6guxg=='
        self.bucket = 'testB'
        self.org = 'ansuman.mohanty@gmail.com'

        try:
            self.client = InfluxDBClient(url=influx_cloud_url, token=influx_cloud_token)
            print("InfluxDB client created...")
        except Exception as e:
            print("Could not create client: {}".format(str(e)))
            sys.exit(0)

        try:
            self.write_api = client.write_api(write_options=SYNCHRONOUS)
            print("InfluxDB write_api created...")
        except Exception as e:
            print("Could not create write API: {}".format(str(e)))
            sys.exit(0)

    def do_set_measurement(self, line):
        self.point = Point(line.args)

    def do_set_tag(self, line):
        self.point.tag(line.arg_list[0], line.arg_list[1])

    def do_set_field(self, line):
        self.point.field(line.arg_list[0], line.arg_list[1])

    def do_print_point(self, line):
        print(self.point)

    def do_write_point(self, line):
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=self.point)
            print("Wrote one point...")
        except Exception as e:
            print("write_points error:[{}] {}".format(e.__class__.__name__, str(e)))
            # client.create_database('ticks')
            sys.exit(0)

    def do_query(self, line):
	"""
	Query written data
	"""
	query = f'from(bucket: "{bucket}") |> range(start: -1d) |> filter(fn: (r) => r._measurement == "{kind}")'
	print(f'Querying from InfluxDB cloud: "{query}" ...')
	print()

	query_api = client.query_api()
	tables = query_api.query(query=query, org=org)

	for table in tables:
	    for row in table.records:
		print(f'{row.values["_time"]}: host={row.values["host"]},device={row.values["device"]} '
		      f'{row.values["_value"]} °C')

	print()
	print('success')

if __name__ == '__main__':
    app = REPL()
    app.cmdloop()
