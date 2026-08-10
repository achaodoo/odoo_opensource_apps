# -*- coding: utf-8 -*-
from odoo import fields, models,api


class AccountMove(models.Model):
    _inherit = "account.move"

    state = fields.Selection(
        selection_add=[
            ('waiting_approval', 'Waiting for Approval'),
            ('approved', 'Approved'),('posted', 'Posted'),
            ('rejected', 'Rejected'),
        ],
        ondelete={
            'waiting_approval': 'set default',
            'approved': 'set default',
            'rejected': 'set default',
        },
        help="States of the vendor payment approval workflow.",
    )
    is_register_payment = fields.Boolean(string="Register Payment")

