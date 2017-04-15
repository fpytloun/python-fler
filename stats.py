#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import argparse
import socket
from fler import Fler


def parse_args():
    parser = argparse.ArgumentParser("Fler statistics")
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-d', '--debug', action="store_true")
    parser.add_argument('--private-key', required=True)
    parser.add_argument('--public-key', required=True)
    parser.add_argument('--carbon-host', default="127.0.0.1")
    parser.add_argument('--carbon-port', default=2003, type=int)
    args = parser.parse_args()
    return args


def setup_logging(args):
    lg_root = logging.getLogger('')
    if args.verbose:
        lg_root.setLevel(logging.INFO)

    if args.debug:
        lg_root.setLevel(logging.DEBUG)


def dict2carbon(data, timestamp, path="fler"):
    res = []
    for key, value in data.iteritems():
        if type(value) == dict:
            res.extend(dict2carbon(value, timestamp, "%s.%s" % (path, key)))
        else:
            res.append("%s.%s %s %s" % (path, key, value, timestamp))
    return res


def write_carbon(args, data, timestamp=None):
    if not timestamp:
        timestamp = int(time.time())

    msg = dict2carbon(data, timestamp, path="fler")
    logging.debug("Connected to carbon server %s:%s" % (args.carbon_host, args.carbon_port))
    sock = socket.socket()
    sock.connect((args.carbon_host, args.carbon_port))
    for m in msg:
        logging.debug(m)
        sock.sendall("%s\n" % m)
    sock.close()


def fix_timestamp(ts):
    # Fix some weird timestamps having 2 instead of 1 as the first number
    ts = int(ts)
    if ts > 2490000000:
        ts = ts - 1000000000
    return ts


def main():
    args = parse_args()
    setup_logging(args)
    res = {
        'product': {},
        'account': {},
    }
    fler = Fler((args.private_key, args.public_key))

    # Account info
    account = fler.get_account_info()
    products = fler.get_products()
    stats = fler.request("/seller/statistics/overview")
    res['account'] = {
        'fans': account["seller"]["fans_count"],
        'rank': float(account["seller"]["fler_rank"]),
        'rating_count': account["seller"]["rating_count"],
        'rating_pct': account["seller"]["rating_pct"],
        'likes': stats['likes']['count'],
        'views': {
            'shop': stats['views']['shop'],
            'shop_sold': stats['views']['shop.sold'],
            'profile': stats['views']['profile'],
            'total': stats['views']['total'],
        },
        'orders': {
            'new': stats['orders']['count.new'],
            'finished': stats['orders']['count.finished'],
            'total': stats['orders']['count.total'],
            'accepted': stats['orders']['count.accepted'],
            'paid': stats['orders']['count.paid'],
        },
        'sellrating': {
            'average': stats['sellrating']['average'] or 0,
            'count': stats['sellrating']['count'],
        },
        'turnover': stats['turnover']['total'],
        'flerpost': {
            'new': stats['flerpost']['message.count.new'],
        },
    }
    res['account']['products_available'] = len(products)
    res["account"]["products_sold"] = account["seller"]["products_sold_count"]

    for product in products:
        res['product'][product["id"]] = {
            "category": int(product["category"]),
            "sellcategory": int(product["sellcategory"]),
            "cool": int(product["is_cool"]),
            "craft": int(product["is_craft"]),
            "topable": int(product["is_topable"]),
            "price": float(product["price"]),
            "price_without_prov": float(product["price_without_prov"]),
            "stock": int(product["stock"]),
            "inserted": fix_timestamp(product["ts_ins"]),
            "topped": fix_timestamp(product["ts_top"]),
        }

    write_carbon(args, res)

if __name__ == "__main__":
    main()
