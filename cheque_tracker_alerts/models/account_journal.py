from odoo import models, fields, api, _


class AccountJournal(models.Model):
    """Extend account journals with cheque-related configuration."""
    _inherit = "account.journal"

    is_cheque = fields.Boolean(string='Cheque',default=False)