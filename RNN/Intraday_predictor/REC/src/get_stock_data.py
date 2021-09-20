from datetime import date
from nsepy import get_history

recltd = get_history(symbol='RECLTD',
        start=date(2008,1,1), 
        end=date(2020,1,10))

recltd.to_csv('../data/recltd.csv', header=True)

