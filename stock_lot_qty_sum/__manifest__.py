# -*- coding: utf-8 -*-
{
    "name": "Stock Lot - Grouped SUM for Computed Fields",
    "version": "17.0.1.0.0",
    "summary": "Enables SUM aggregation on non-stored computed fields (e.g., product_qty) in grouped list views.",
    "description": """
Stock Lot - Grouped SUM for Non-Stored Computed Fields
======================================================

This module extends Odoo's default grouping behavior by enabling SUM
aggregation on non-stored computed fields like `product_qty` in the
`stock.lot` model. Odoo normally cannot aggregate such fields at the SQL
level, so this module computes them manually in Python and injects them
into grouped list view results.

Key Features:
-------------
- Supports `product_qty:sum` in list view groupings.
- Python-level SUM calculation for computed fields.
- Seamless integration with standard read_group behavior.
    """,
    "author": "Achaodoo",
    "maintainer": "Achaodoo",
    "website": "https://achaodoo.com/",
    "license": "LGPL-3",
    "category": "Inventory",
    "depends": ["stock"],
    "images": ['static/description/banner.png'],
    "data": [
    ],
    "support": "hello.achaodoo@gmail.com",
    "installable": True,
    "application": False,
    "auto_install": False,
}