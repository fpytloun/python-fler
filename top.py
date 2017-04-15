#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import argparse
from fler import Fler


def parse_args():
    parser = argparse.ArgumentParser("aptly-publisher")
    parser.add_argument('-v', '--verbose', action="store_true")
    parser.add_argument('-d', '--debug', action="store_true")
    parser.add_argument('--private-key', required=True)
    parser.add_argument('--public-key', required=True)
    args = parser.parse_args()
    return args


def setup_logging(args):
    lg_root = logging.getLogger('')
    if args.verbose:
        lg_root.setLevel(logging.INFO)

    if args.debug:
        lg_root.setLevel(logging.DEBUG)


def main():
    args = parse_args()
    setup_logging(args)

    fler = Fler((args.private_key, args.public_key))

    topped = []
    topable = fler.get_topable()
    for product in topable:
        try:
            fler.top(product['id'])
            topped.append(product['id'])
        except Exception as e:
            if e.error == "Topování není dostupné":
                break

    logging.info("Script finished, topped %s products: %s" % (len(topped), topped))

if __name__ == "__main__":
    main()
