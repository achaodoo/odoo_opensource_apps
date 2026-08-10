# -*- coding: utf-8 -*-

from odoo import fields, models


class VendorPaymentRejectWizard(models.TransientModel):
    """Wizard used to capture the reason for rejecting a vendor payment."""

    _name = "vendor.payment.reject.wizard"
    _description = "Vendor Payment Rejection"

    reason = fields.Text(
        string="Reason",
        required=True,
    )

    def action_confirm(self):
        """Reject the vendor payment with the entered reason.

        Returns:
            dict: Action to close the wizard.
        """
        self.ensure_one()

        payment_id = self.env.context.get("active_id")
        payment = self.env["account.payment"].browse(payment_id)

        if payment.exists():
            payment.write({
                "reject_reason": self.reason,
                "state": "rejected",
            })

            if payment.vendor_bill_id:
                payment.vendor_bill_id.is_register_payment = False

        return {"type": "ir.actions.act_window_close"}