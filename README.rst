==================================
Fler API Python client and scripts
==================================

Scripts
=======

Automatically top items
-----------------------

Script ``top.py`` can be used to automatically top items, it works in a
following way:

- get current user's fler rank to find out how often one can top
- list products that is possible to top and sort them by last top date from
  older to newer
- top one by one until we receive an exception (hit our daily limit)

In this way all items will get topped during the time.
It's simple to customize the script to filter by category and top only some
items.
