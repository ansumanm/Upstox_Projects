from datetime import date
from nsepy import get_history

nifty = get_history(symbol='NIFTY',
        start=date(2008,1,1), 
        end=date(2020,1,10),
        index=True)

nifty.to_csv('../data/nifty.csv', header=True)

