from datetime import date
from nsepy import get_history

recltd = get_history(symbol='TCS',
        start=date(2003,1,1), 
        end=date(2020,1,10))

recltd.to_csv('../data/stock_data.csv', header=True)

