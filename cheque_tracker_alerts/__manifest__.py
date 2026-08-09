# -*- coding: utf-8 -*-

{
    'name': 'Cheque Tracker Status',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'author': 'Achaodoo',
    'website': 'https://achaodoo.com',
    'summary': 'Track cheques, PDC/CDC status and automated alerts',
    'description': """
Cheque Tracker Status
=====================

Track and manage cheque payments with PDC/CDC status,
cheque dates, configurable alerts, email notifications,
and cheque tracking reports.

Features:
- Track cheque payments
- PDC and CDC status management
- Configure cheque alert periods
- Automatic email notifications
- Incoming and outgoing cheque tracking
- Cheque tracker PDF report
- Date-based cheque status updates
""",
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/cheque_tracker_status_cron.xml',
        'data/mail_template_data.xml',
        'views/account_journal_views.xml',
        'views/cheque_tracker_status_views.xml',
        'views/account_payment_views.xml',
        'wizard/cheque_tracker_report.xml',
        'report/cheque_tracker_status_templates.xml',
        'report/check_tracker_status_report.xml',
        'views/cheque_tracker_status_menus.xml',
    ],
    "images": ["static/description/banner.png"],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}