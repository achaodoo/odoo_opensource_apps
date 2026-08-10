# -*- coding: utf-8 -*-

from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payment_vals_from_wizard(self, vals):
        rec = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(vals)

        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')

        if active_id and active_model == 'account.move.line' and 'expense_sheet_register_payment' not in self.env.context and 'hr_payroll_payment_register' not in self.env.context:
            move = self.env['account.move'].browse(active_id)

            if move and move.move_type == 'in_invoice':
                rec['vendor_bill_id'] = move.id

        return rec

    def _post_payments(self, to_process, edit_mode=False):
        """Send vendor payments for approval instead of posting immediately."""
        payments = self.env["account.payment"]

        for vals in to_process:
            payments |= vals["payment"]

        if self.env.context.get("is_credit_note"):
            payments.action_post()
        else:
            payments.action_send_for_approval()



