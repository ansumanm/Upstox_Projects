from datetime import date
from nsepy import get_history

bnf = get_history(symbol='NIFTY BANK',
        start=date(2008,1,1), 
        end=date(2020,1,10),
        index=True)

bnf.to_csv('../data/banknifty.csv', header=True)

