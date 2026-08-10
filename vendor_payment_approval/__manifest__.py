# -*- coding: utf-8 -*-
{
    'name': 'Vendor Payment Approval',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'author': 'Achaodoo',
    'website': 'https://achaodoo.com',
    'summary': 'Require approval before posting vendor payments',
    'description': """
Vendor Payment Approval
=======================

Adds an approval workflow for vendor payments before they are posted.

Key Features:
- Submit vendor payments for approval.
- Allow authorized users to self-assign payments.
- Approve or reject vendor payments.
- Capture rejection reasons.
- Notify approvers by email.
- Notify accountants after approval.
- Prevent direct posting before approval.
""",
    'depends': ['account'],
    "images": ['static/description/banner.png'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'wizard/vendor_payment_reject_wizard_views.xml',
        'views/account_payment_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_register_views.xml',
    ],
    "support": "hello.achaodoo@gmail.com",
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
