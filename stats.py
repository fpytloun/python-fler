#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import argparse
import json
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
    for m in msg:
        logging.debug(m)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto("%s\n" % m, (args.carbon_host, args.carbon_port))
        sock.close()


def main():
    args = parse_args()
    setup_logging(args)
    res = {
        'product': {},
        'account': {},
    }
    fler = Fler((args.private_key, args.public_key))

    # Account info
    info = fler.get_account_info()
    products = fler.get_products()
    res['account'] = {
        'fans': info["seller"]["fans_count"],
        'rank': float(info["seller"]["fler_rank"]),
        'rating_count': info["seller"]["rating_count"],
        'rating_pct': info["seller"]["rating_pct"],
    }
    res['account']['products_available'] = len(products)
    res["account"]["products_sold"] = info["seller"]["products_sold_count"]

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
            "inserted": int(product["ts_ins"]),
            "topped": int(product["ts_top"]),
        }

    write_carbon(args, res)

if __name__ == "__main__":
    main()
