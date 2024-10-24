# Stock portfolio simulator in shell

Buy, hold and sell stocks with fake money. Super simple shell / python app.

## Install

```
pip3 install -r requirements.txt
chmod u+x salkku.py
```

## Add funds
```
./salkku.py --add_funds --amount 5000
```

## Buy stocks

Use stock names according to Yahoo Finance

```
./salkku.py --buy --stock TSLA --amount 10
```

## Sell stocks

```
./salkku.py --sell --stock TSLA --amount 10
```

## Show portfolio

```
./salkku.py -l
```

## Limits

 - No support for currencies (yet?)
 - No order book simulation
 - No shorting
