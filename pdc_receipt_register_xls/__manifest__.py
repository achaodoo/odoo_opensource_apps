# -*- coding: utf-8 -*-
{
    'name': 'PDC Receipt Register Report',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'author': 'Achaodoo',
    'website': 'https://achaodoo.com',
    'support': 'hello.achaodoo@gmail.com',
    'summary': 'Generate PDC receipt register reports in XLSX format',
    'description': """
        Generate an XLSX PDC receipt register report based on a selected
        date range and bank journal.
    """,
    'depends': ['account','cheque_tracker_alerts'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/pdc_receipt_register_report.xml',
        'views/pdc_receipt_register_xls_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
