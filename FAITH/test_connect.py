import cx_Oracle

host='10.243.122.170'
port='1521'
service='ORCLPDB'
userid='market'
password='welcome'

dsn_tns = cx_Oracle.makedsn(host, port, service_name=service) 
conn = cx_Oracle.connect(user=userid, password=password, dsn=dsn_tns) 

c = conn.cursor()

"""
query = 'select * from Market."eq_eod"'
c.execute(query) 

for row in c:
    print(row)
"""

# query = 'select USERNAME from SYS.ALL_USERS'
query = "SELECT table_name FROM all_tables where owner  = 'MARKET'"
print(query)
c.execute(query) 
for row in c:
    print(row)


conn.close()
