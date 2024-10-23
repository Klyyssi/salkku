#!/usr/bin/env python3

import os
import json
import argparse
import yfinance as yf
import time
from datetime import datetime
from operator import itemgetter

cfg_path = "salkkuconfig.json"

def write_config(cfg):
    with open(cfg_path, "w") as out:
        out.write(json.dumps(cfg))

def create_config():
    default_config = {
        'COMMISSION_PERCENTAGE': 0.2,
        'COMMISSION_MINIMUM': 10,
        'COMMISSION_PAID': 0,
        'FUNDS': 0,
        'PORTFOLIO': {},
        'HISTORY': []
    }
    write_config(default_config)
    return default_config

def get_last_tick(stock):
    try:
        stock = yf.Ticker(stock)
        return stock.info['currentPrice']
    except:
        return None

def get_stock_prices(cfg):
    prices = {}
    for stock in cfg['PORTFOLIO']:
        prices[stock] = get_last_tick(stock)
    return prices

def get_market_value(cfg, prices):
    market_value = 0
    for stock in cfg['PORTFOLIO']:
        market_value += prices[stock] * cfg['PORTFOLIO'][stock]['amount']
    return market_value

def get_added_funds(cfg):
    funds = 0
    for row in cfg['HISTORY']:
        if row['type'] == 'ADD_FUNDS':
            funds += row['amount']
    return funds

def timestamp():
    return datetime.fromtimestamp(time.time()).isoformat()

def add_funds(cfg, amount):
    cfg['FUNDS'] += amount
    cfg['HISTORY'].append({ 'type': 'ADD_FUNDS', 'amount': amount, 'date': timestamp() })
    write_config(cfg)
    print(json.dumps(cfg['HISTORY'][-1], indent=2))

def add_to_portfolio(cfg, stock, amount, price):
    if stock in cfg['PORTFOLIO']:
        stock_details = cfg['PORTFOLIO'][stock]
        stock_details['amount'] += amount
        stock_details['avg_buy_price'] = (stock_details['avg_buy_price'] * stock_details['amount'] + amount * price) / (amount + stock_details['amount'])
    else:
        cfg['PORTFOLIO'][stock] = { 'amount': amount, 'avg_buy_price': price }

def remove_from_portfolio(cfg, stock, amount):
    curr_amount = cfg['PORTFOLIO'][stock]['amount']
    if amount > curr_amount:
        print(f'Amount too large. You own {curr_amount} stocks.')
        exit(1)
    cfg['PORTFOLIO'][stock]['amount'] -= amount
    if cfg['PORTFOLIO'][stock]['amount'] == 0:
        del cfg['PORTFOLIO'][stock]

def buy(cfg, stock, amount):
    if not amount:
        print('Amount must be greater than 0')
        exit(1)
    price = get_last_tick(stock)
    if not price:
        print(f'Stock {stock} not found')
        exit(1)
    total = price * amount
    commission = max(cfg['COMMISSION_PERCENTAGE'] / 100 * total, cfg['COMMISSION_MINIMUM'])
    if cfg['FUNDS'] < commission + total:
        funds = cfg['FUNDS']
        print(f'You cannot afford that. Your funds: {funds:.2f}, funds required: {total + commission}.')
        exit(1)
    add_to_portfolio(cfg, stock, amount, price)
    cfg['FUNDS'] -= total + commission
    cfg['COMMISSION_PAID'] += commission
    cfg['HISTORY'].append({ 'type': 'BUY', 'stock': stock, 'amount': amount, 'price': price, 'total': total, 'commission': commission, 'date': timestamp() })
    write_config(cfg)
    funds = cfg['FUNDS']
    print(json.dumps(cfg['HISTORY'][-1], indent=2))

def sell(cfg, stock, amount):
    if not amount:
        print('Amount must be greater than 0')
        exit(1)
    if stock not in cfg['PORTFOLIO']:
        print(f'You do not own stock {stock}')
        exit(1)
    price = get_last_tick(stock)
    if not price:
        print(f'Stock {stock} not found')
        exit(1)
    total = price * amount
    commission = max(cfg['COMMISSION_PERCENTAGE'] / 100 * total, cfg['COMMISSION_MINIMUM'])
    profit = price * amount - cfg['PORTFOLIO'][stock]['avg_buy_price'] * amount
    if cfg['FUNDS'] + total < commission:
        print(f'You cannot afford that. Commission is higher than available funds and stock market value.')
        exit(1)
    remove_from_portfolio(cfg, stock, amount)
    cfg['FUNDS'] += total - commission
    cfg['COMMISSION_PAID'] += commission
    cfg['HISTORY'].append({ 'type': 'SELL', 'stock': stock, 'amount': amount, 'profit': profit, 'price': price, 'total': total, 'commission': commission, 'date': timestamp() })
    write_config(cfg)
    print(json.dumps(cfg['HISTORY'][-1], indent=2))
    
def search(stock):
    price = get_last_tick(stock)
    if not price:
        print(f'Stock {stock} not found')
    else:
        print(f'Current price of stock {stock} is {price}')

def list_details(cfg):
    print('History')
    for row in cfg['HISTORY']:
        type, amount, date = itemgetter('type', 'amount', 'date')(row)
        if type == 'SELL':
            stock = row['stock']
            profit = row['profit']
            print(f' - {type} {stock} {amount} {profit:.2f} {date}')
        elif type == 'BUY':
            stock = row['stock']
            print(f' - {type} {stock} {amount} {date}')
        else:
            print(f' - {type} {amount} {date}')
    print('\nCommission percentage:', cfg['COMMISSION_PERCENTAGE'])
    print('Commission minimum:', cfg['COMMISSION_MINIMUM'])
    print('Commissions paid:', cfg['COMMISSION_PAID'])
    added_funds = get_added_funds(cfg)
    if added_funds == 0:
        exit(0)
    print('\nTotal added funds:', added_funds)
    funds = cfg['FUNDS']
    print(f'Available funds: {funds:.2f}')
    stock_prices = get_stock_prices(cfg)
    market_value = get_market_value(cfg, stock_prices)
    print(f'\nMarket value: {market_value:.2f}')
    total_val = market_value + cfg['FUNDS']
    percentage = ((total_val / added_funds) - 1) * 100
    print(f'Total value: {total_val:.2f} ({percentage:.2f}%)')
    print('\nYour portfolio')
    print('Stock\t\tAmount\tPrice\tProfit')
    for stock in cfg['PORTFOLIO']:
        amount, avg_buy_price = itemgetter('amount', 'avg_buy_price')(cfg['PORTFOLIO'][stock])
        price = stock_prices[stock]
        profit = price * amount - avg_buy_price * amount
        profit_percentage = (price / avg_buy_price - 1) * 100
        stock_adjusted = stock.ljust(10)
        print(f'{stock_adjusted}\t{amount}\t{price:.2f}\t{profit:.2f} ({profit_percentage:.2f}%)')

def main():
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as js:
            cfg = json.load(js)
    else:
        cfg = create_config()
    
    parser = argparse.ArgumentParser(
                    prog='Salkku',
                    description='Simulate buy, hold and sell stocks')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--buy', action='store_true')
    group.add_argument('--sell', action='store_true')
    group.add_argument('--add_funds', action='store_true')
    group.add_argument('-l', '--list', action='store_true')
    group.add_argument('--search', action='store_true')
    parser.add_argument('--stock')
    parser.add_argument('-a', '--amount', type=int)
    args = parser.parse_args()

    if args.add_funds:
        add_funds(cfg, args.amount)
    if args.list:
        list_details(cfg)
    if args.buy:
        buy(cfg, args.stock, args.amount)
    if args.sell:
        sell(cfg, args.stock, args.amount)
    if args.search:
        search(args.stock)

if __name__ == '__main__':
    main()
