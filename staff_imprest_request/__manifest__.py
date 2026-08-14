# -*- coding: utf-8 -*-
{
    'name': "Staff Imprest Request & Approval",
    'summary': "Manage staff imprest requests with multi-level approval",
    'description': """
        Staff Imprest Request & Approval helps organizations manage employee
        imprest requests through a structured approval workflow.

        Employees can submit imprest requests with the required amount and
        purpose. Requests can then be reviewed and approved by the designated
        HOD and Finance Manager.

        Key features include:
        - Staff imprest request creation
        - HOD approval workflow
        - Finance Manager approval workflow
        - Request rejection with a rejection reason
        - Email notifications for approval requests
        - Approval and rejection status tracking
        - Payment action after final approval
        - User and role assignment
        - Chatter-based request communication and activity tracking
    """,

    'author': 'Achaodoo',
    'website': 'https://achaodoo.com',
    'support': 'hello.achaodoo@gmail.com',
    'category': 'Human Resources/Expenses',
    'version': '17.0.1.0.0',
    'depends': [
        'account',
        'hr_expense',
        'mail',
    ],
    'data': [
        'security/staff_imprest_groups.xml',
        'security/ir.model.access.csv',
        'security/staff_imprest_request_security.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'wizard/reject_reason_views.xml',
        'views/account_journal_views.xml',
        'views/staff_imprest_request_views.xml',
        'views/staff_imprest_request_menus.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

