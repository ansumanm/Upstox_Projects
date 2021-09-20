import sys
import cmd
import cx_Oracle
from datetime import date
from sqlalchemy import create_engine, inspect
from nsepy import get_history
import pandas as pd

host='10.243.122.170'
port='1521'
service='ORCLPDB'
userid='market'
password='welcome'

oracle_connection_string = (
        'oracle+cx_oracle://{username}:{password}@' +
        cx_Oracle.makedsn('{hostname}', '{port}', service_name='{service_name}')
        )

try:
    engine = create_engine(
            oracle_connection_string.format(
                username=userid,
                password=password,
                hostname=host,
                port=port,
                service_name=service,
                )
            )
except Exception as e:
    print("Failed to create engine: {}".format(e))
    sys.exit(0)

# query = 'select USERNAME from SYS.ALL_USERS'
# query = "SELECT table_name FROM all_tables where owner  = 'MARKET'"
class OracleCLI(cmd.Cmd):
    """Simple command line interface."""
    def do_SELECT(self, query):
        query_str = "SELECT " + query
        try:
            df = pd.read_sql_query(query_str, engine)
        except Exception as e:
            print(str(e))
            return

        print(df)

    def do_select(self, query):
        query_str = "SELECT " + query
        try:
            df = pd.read_sql_query(query_str, engine)
        except Exception as e:
            print(str(e))
            return

        print(df)

    def do_get_from_nse(self, scrip):
        print('Fetching data from NSE...')
        try:
            scrip_history = get_history(symbol=scrip,
                    start=date(2008,1,1), 
                    end=date(2020,1,10))
        except Exception as e:
            print('Failed to get scrip history: {}'.format(str(e)))
            sys.exit(0)

        # Make a local copy of the scrip
        scrip_history.to_csv('%s.csv' % scrip, header=True)
        print('Saved data to %s.csv' % scrip)

    def do_write_to_db(self, scrip):
        csv_file = '%s.csv' % scrip
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print('Failed to read %s: %s' % (csv_file, str(e)))
            return

        print('Writing to DB...')
        try:
            df.to_sql('eq_eod', con=engine, if_exists='replace')
        except Exception as e:
            print('Failed to write to db: %s' % str(e))
            return

        print('Done...')


    def do_EOF(self, line):
        print("Bye Bye...")
        return True

    def postloop(self):
        print

if __name__ == '__main__':
    OracleCLI().cmdloop()
