# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_staff_imprest_journal = fields.Boolean(default=False,string="Staff Imprest Journal",)