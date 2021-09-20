from datetime import date
from nsepy import get_history
from nsepy.derivatives import get_expiry_date
# expiry = get_expiry_date(year=2015, month=1)
expiry_date = get_expiry_date(year=2019, month=1)

nifty_fut = get_history(symbol="NIFTY",
                        start=date(2019,8,1),
                        # end=date(2019,8,10),
			end=expiry_date,
                        index=True,
                        futures=True,
                        expiry_date=expiry_date)
