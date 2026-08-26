# -*- coding: utf-8 -*-
{
    'name': 'PDC Payment Register Report',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'author': 'Achaodoo',
    'website': 'https://achaodoo.com',
    'support': 'hello.achaodoo@gmail.com',
    'summary': 'Generate PDC payment register reports in Excel format',

    'description': """
PDC Payment Register Report
============================

Generate a professional Excel (XLSX) report for outgoing Post-Dated
Cheque (PDC) payments.

Key Features:
-------------
* Generate PDC payment register reports in Excel format.
* Filter payments by date range.
* Filter payments by bank journal.
* Show payment voucher number and vendor details.
* Show payment reference.
* Show bank account details.
* Show cheque date.
* Show payment amount and total amount.
* Include only PDC payments that require cheque tracker alerts.

Dependency:
-----------
This module depends on the "Cheque Tracker Alerts" module.

The Cheque Tracker Alerts module provides PDC/CDC cheque tracking,
cheque dates, configurable alert settings, and cheque tracker statuses.

Please install the Cheque Tracker Alerts module before installing
this module.

Available on the Achaodoo Odoo Apps Store.
""",
    'depends': ['account', 'cheque_tracker_alerts'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/pdc_payment_register_report.xml',
        'views/pdc_payment_register_xls_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
