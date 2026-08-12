# -*- coding: utf-8 -*-
{
    'name': 'Summary Sales Book Report',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Generate detailed sales book reports in Excel',
    'author': 'Achaodoo',
    'website': 'https://achaodoo.com',
    'support': 'hello.achaodoo@gmail.com',
    'description': """
Summary Sales Book Report
=========================

Generate a detailed Sales Book report in Excel based on a selected date range.

The report includes:

- Invoice Date
- Invoice Number
- Customer
- Sales Account
- Narration
- Amount
- VAT
- Invoice Value
    """,
    'depends': [
        'account',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/summary_sales_book_report.xml',
        'views/summary_sales_book_report_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}