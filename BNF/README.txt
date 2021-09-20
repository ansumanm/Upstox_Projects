Banknifty algo trading
======================

Volume Breakout setup v1:
-------------------------
Entry: a) When last 1 min volume > 40K
       b) When is a BULL candle.
Target: 40 points
SL: Volume candle classical pivot s1/r1

Volume Breakout setup v2(Advanced):
-----------------------------------
Maintain a Volume state machine:
Study 10 sec volume break out behavior.
Low Volume ---> High Volume: Entry


Websocket hack:
================
Was getting SSL certificate error. So made the following code change
that worked.

1) Installed 

pip install websocket-client==0.55.0

2) Made the following change:

~/upstox_env/lib/python3.6/site-packages/websocket/_app.py
343                    # callback(*args)
344                    callback(self, *args)


