#!/usr/bin/env python3

"""
Gamma scalping.

Strategy:
1) Buy 10 ATM PEs
2) Buy 5 Futs
3) When the Banknifty FUT falls by 100 points, (Banknifty options strike distance), buy 1 Banknifty FUT.
4) When the Banknifty FUT rises by 100 points, SELL one Banknifty FUT.

Implementation:
==============
1) Subscribe to Banknifty FUT
2) Determine ATM PE according to BNF index, subscribe to it.
3) Place the orders in the system
    a) BUY order at higher strike.
    a) SELL order at lower strike.
4) Wait for the notification of the order to be fulfilled.
5) After BUY/SELL is fulfilled, we have to wait for the price to cross another strike.

Strikes marked w.r.t PE.

---- ITM2

---- ITM1

---- ATM

---- OTM1

---- OTM2
Basically, we SELL at ITMs and BUY at OTMs.
For each SELL order, we place a BUY order at a lower strike, and for each BUY order, we place a SELL order
at the higher strike.
Our Options position will be constant. We need to track the Future positions only.
"""
