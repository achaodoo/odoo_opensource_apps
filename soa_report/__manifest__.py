# -*- coding: utf-8 -*-
{
    'name': 'SOA Report',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Generate customer Statement of Account reports',
    'author': 'Achaodoo',
    'website': 'https://achaodoo.com',
    'support': 'hello.achaodoo@gmail.com',
    'description': """
SOA Report
=========

Generate customer Statement of Account reports with a selected
customer and as-on date.

The report supports PDF and XLSX formats and allows sending
the statement by email.
    """,
    'depends': ['account', 'report_xlsx', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'report/soa_pdf_report_template.xml',
        'report/soa_report.xml',
        'wizard/soa_report_views.xml',
        'wizard/mail_compose_message_views.xml',
        'views/soa_report_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
}