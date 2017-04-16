# -*- coding: utf-8 -*-

import time
import base64
from Crypto.Hash import SHA, HMAC
import requests
from urlparse import urlparse, urljoin
import logging
from datetime import datetime, timedelta


class Fler(object):
    # { rank: (number of tops per day, timedelta between tops) }
    # https://www.fler.cz/napoveda?scat=4&cat=3&id=2
    top_config = {
        0: (3, timedelta(hours=8)),
        50: (3.4, timedelta(hours=7)),
        80: (4, timedelta(hours=6)),
        95: (4.8, timedelta(hours=5)),
        97: (6, timedelta(hours=4)),
        99: (8, timedelta(hours=3)),
        99.5: (12, timedelta(hours=2)),
    }

    product_fields = (
        "title",
        "variant_share_main_photo",
        "description",
        "price",
        "stock",
        "stock_unit",
        "delivery",
        "post1",
        "post2",
        "category",
        "sell_to_eu",
        "is_visible",
        "sellcategory",
        "intern_code",
        "keywords_tech",
        "keywords_mat",
        "keywords_tag",
        "colors",
        "product_weight",
        "product_vat_mode",
        "quicksell",
        "note_text",
        "note_flag",
        "reserve_for_username",
        "reserve_for_uid",
        "is_variant",
        "is_variant_master",
        "id_variant_master",
        "provision_pct",
        "is_cool",
        "is_craft",
        "ts_top",
        "ts_ins",
        "url",
        "currency",
        "photo_main",
        "photo_other",
        "is_topable",
        "other_currencies",
    )

    def __init__(self, key, server="https://www.fler.cz"):
        self.server = server
        self.key_private = key[0]
        self.key_public = key[1]

    def _sign(self, string):
        to_sign = string.encode("utf-8")
        hmac = HMAC.new(self.key_private, to_sign, SHA)
        return base64.b64encode(hmac.hexdigest())

    def request(self, path, method="GET", headers={}, payload={}, parse_json=True):
        timestamp = int(time.time())
        url = urljoin(self.server, "/api/rest%s" % path)
        path = urlparse(url).path
        req_string = self._sign("%s\n%s\n%s" % (method, timestamp, path))
        auth_string = "API1 %s %s %s" % (self.key_public, timestamp, req_string)
        headers.update({"X-FLER-AUTHORIZATION": auth_string})

        logging.info("%s %s, payload=%s" % (method, url, payload))
        if method == "GET":
            ret = requests.get(url, headers=headers, params=payload)

        if parse_json:
            try:
                json = ret.json()
            except Exception:
                raise FlerApiException(ret.text, response=ret)
            self._check_error(json)
            return json

    def _check_error(self, ret):
        if type(ret) == dict and (ret.get("error") or ret.get("error_number")):
            raise FlerApiException(**ret)

    def ping(self):
        return self.request("/seller/ping")

    def get_account_info(self):
        return self.request("/user/account/info")

    def get_products(self, id=None, fields=None, status="STATUS_AVAILABLE",
                     sort="NAME", sort_reverse=False, extended=False):
        # https://www.fler.cz/uzivatel/nastroje/flerapi?view=docs&url=%2Fapi%2Frest%2Fseller%2Fproducts%2Flist
        if not fields:
            fields = self.product_fields

        payload = {}
        if id:
            payload["id"] = id
        else:
            if fields:
                payload["fields"] = ','.join(str(i) for i in fields)
            if status:
                payload["type"] = status
            if sort:
                payload["sort"] = sort

        if extended:
            payload["conf"] = "extended_info"

        products = self.request("/seller/products/list", payload=payload)
        if sort_reverse:
            products.reverse()
        return products

    def top(self, id):
        return self.request("/seller/products/action/top", payload={"id": id})

    def get_topable(self, **kwargs):
        if "fields" not in kwargs:
            kwargs['fields'] = []

        if "sort" not in kwargs:
            kwargs['sort'] = "TOP_DATE"
            kwargs['sort_reverse'] = True

        for field in ["is_topable", "ts_top"]:
            if field not in kwargs['fields']:
                kwargs['fields'].append(field)

        top_config = self.get_top_config()
        ret = self.get_products(**kwargs)
        products = []
        for product in ret:
            if bool(product["is_topable"]):
                last_top = datetime.fromtimestamp(float(self.fix_timestamp(product["ts_top"])))
                next_top = last_top + top_config[1]
                if next_top <= datetime.now():
                    products.append(product)
        return products

    def get_top_config(self):
        info = self.get_account_info()
        rank = float(info["seller"]["fler_rank"])
        for level, conf in self.top_config.iteritems():
            if rank >= level:
                return self.top_config[level]

    def fix_timestamp(self, ts):
        # Fix some weird timestamps having 2 instead of 1 as the first number
        ts = int(ts)
        if ts > 2490000000:
            ts = ts - 1000000000
        return ts


class FlerApiException(Exception):
    def __init__(self, *args, **kwargs):
        self.response = kwargs.pop('response', None)
        self.request = kwargs.pop('request', None)
        if (self.response is not None and not self.request and
                hasattr(self.response, 'request')):
            self.request = self.response.request
        self.error = kwargs.pop('error', None)
        if type(self.error) == list:
            self.error = self.error[0].encode("utf-8")
        elif type(self.error) == str:
            self.error = self.error.encode("utf-8")
        self.error_number = kwargs.pop('error_number', None)
        if not args:
            args = ["%s, error_number=%s" % (self.error, self.error_number)]
        super(Exception, self).__init__(*args, **kwargs)
