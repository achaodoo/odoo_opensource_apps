# -*- coding: utf-8 -*-
{
    'name': 'Purchase Order Follower Notification Control',
    'version': '17.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Control follower email notifications on purchase orders',
    'description': """
Purchase Order Follower Notification Control
=============================================

Control email notifications sent to followers of Purchase Orders.

This module helps prevent unwanted follower notifications when working
with Purchase Orders while preserving the standard Odoo purchase workflow.
    """,
    "author": "Achaodoo",
    "maintainer": "Achaodoo",
    "website": "https://achaodoo.com/",
    "license": "LGPL-3",
    "support": "hello.achaodoo@gmail.com",
    "images": ["static/description/banner.png"],
    'depends': ['purchase'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}