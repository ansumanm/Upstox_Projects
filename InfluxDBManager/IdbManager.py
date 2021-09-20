#!/usr/bin/env python3
import os
import atexit
import readline
from cmd2 import Cmd
from influxdb import InfluxDBClient

history_file = os.path.expanduser('~/.IDB_history')
if not os.path.exists(history_file):
    with open(history_file, "w") as fobj:
        fobj.write("")
readline.read_history_file(history_file)
atexit.register(readline.write_history_file, history_file)

# "q=SELECT%20last(%22ltp%22)%20FROM%20%22FeedFull%22%20WHERE%20time%20%3E%3D%20now()%20-%205m%20GROUP%20BY%20time(10s)%20fill(null)"

class REPL(Cmd):
    prompt = "IDB> "
    intro = """
	InfluxDB Manager CLI 
    """

    def __init__(self):
        Cmd.__init__(self)
        self.host = 'localhost'
        self.port = '8086'
        self.client = InfluxDBClient(host=self.host, port=self.port)
        self.db_name = 'testdb'
        self.point = {}

    def do_set_db(self, line):
        self.db_name = line
        self.client = InfluxDBClient(host=self.host, port=self.port, database=self.db_name)

    def do_set_db_host(self, line):
        self.host = line
        print("""
        Host set to {} ...
        """.format(self.host))

    def do_set_db_port(self, line):
        self.port = line
        print("""
        Port set to {} ...
        """.format(self.port))

    def do_get_server_info(self, line):
        print("""
        host: {}
        port: {}
        """.format(self.host, self.port))

    def do_create_client(self, line):
        self.client = InfluxDBClient(host=self.host, port=self.port)
        print("""
        Created client...
        """)

    def do_get_db_list(self, line):
        try:
            print(self.client.get_list_database())
        except Exception as e:
            print(""" Exception: {}""".format(str(e)))

    def do_create_db(self, line):
        try:
            self.client.create_database(line)
            self.db_name = line
        except Exception as e:
            print(""" Exception: {}""".format(str(e)))

    def do_set_measurement(self, line):
        print(line)
        print(type(line))
        self.point["measurement"] = line.args

    def do_set_tag(self, line):
        self.point["tags"] = eval(line)

    def do_set_fields(self, line):
        self.point["fields"] = eval(line)

    def do_print_point(self, line):
        print(self.point)

    def do_write_point(self, line):
        try:
            self.client.write_points([self.point], database=self.db_name)
        except Exception as e:
            print("""
            Exception: {}
            """.format(str(e)))

    def do_drop_db(self, line):
        try:
            self.client.drop_database(line)
        except Exception as e:
            print("""
            Exception: {}
            """.format(str(e)))

    def do_drop_measurement(self, line):
        try:
            self.client.drop_measurement(line)
        except Exception as e:
            print("""
            Exception: {}
            """.format(str(e)))

    def do_delete_series(self, line):
        pass

    def do_query(self, line):
        time_str = " time >= 1587095100000ms and time <= 1587117600000ms"

        query = 'SELECT last("ltp") AS "Close",\
                max("ltp") AS "High",\
                min("ltp") AS "Low", \
                first("ltp") AS "Open",\
                last("atp") AS "ATP",\
                moving_average(mean("ltp"), 20) AS "MA20",\
                moving_average(mean("ltp"), 10) AS "MA10",\
                derivative(moving_average(mean("ltp"), 20), 1m) AS "DeltaMA", \
                moving_average(derivative(moving_average(mean("ltp"), 20), 1m), 10) AS "MADeltaMA" \
                FROM "FeedFull" WHERE ("symbol" =~ /^%s$/) AND %s GROUP BY time(1m)' % (line, time_str)

        result = self.client.query(query)
        print(result)


    def do_ping(self, line):
        try:
            print(self.client.ping())
        except Exception as e:
            print("""
            Exception: {}
            """.format(str(e)))

if __name__ == '__main__':
    app = REPL()
    app.cmdloop()
