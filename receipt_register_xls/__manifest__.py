# -*- coding: utf-8 -*-
{
    'name': 'Receipt Register Report',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Generate receipt registers in Excel with date and customer filters',
    'description': """
Receipt Register Report
=======================

Generate an Excel receipt register for posted customer payments within a
selected date range.

Features:
- Filter receipts by date range.
- Filter by one or more customers.
- Include posted inbound payments from bank and cash journals.
- Export receipt details in XLSX format.
- Show receipt number, customer, narration, destination account,
  state, and amount.
- Display the total receipt amount.
- Use standard Odoo Accounting data.
""",
    'author': 'Achaodoo',
    'website': 'https://achaodoo.com',
    'support': 'hello.achaodoo@gmail.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/receipt_register_report.xml',
        'views/receipt_register_xls_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
