# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    is_vendor_approval = fields.Boolean(string="Vendor Approval", copy=False)
    account_invoice_line = fields.Many2one('account.move.line', string='Account Invoice line', ondelete='cascade')

    def _create_payment_vals_from_wizard(self,batch_result):
        # OVERRIDE
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals['is_vendor_approval'] = True if self.payment_type=='outbound' else False
        payment_vals['account_invoice_line'] = self.account_invoice_line if self.payment_type=='outbound' else False
        return payment_vals

    def action_create_payments(self):
        """Create payments and mark vendor bills as having a registered payment."""
        result = super().action_create_payments()

        if (
                "params" not in self.env.context
                and self.env.context.get("active_model") == "account.move.line"
        ):
            move_lines = self.env["account.move.line"].browse(
                self.env.context.get("active_ids", [])
            )

            vendor_bills = move_lines.mapped("move_id").filtered(
                lambda move: move.move_type in ("in_invoice", "in_refund")
            )

            vendor_bills.write({
                "is_register_payment": True,
            })

        return result
