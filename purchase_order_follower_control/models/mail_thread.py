# -*- coding: utf-8 -*-
from odoo import models


class MailThread(models.AbstractModel):
    """Extend mail.thread to control Purchase Order notifications."""

    _inherit = "mail.thread"

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        """Compute recipients to notify for Purchase Orders.

        For Purchase Orders, restricts the notification recipients to the
        partners explicitly included in the message's ``partner_ids``.
        Other models continue to use Odoo's standard notification behavior.
        """
        recipient_data = super()._notify_get_recipients(
            message, msg_vals, **kwargs
        )

        if self._name == "purchase.order":
            partner_ids = (
                msg_vals.get("partner_ids", [])
                if msg_vals
                else message.sudo().partner_ids.ids
            )

            recipient_data = [
                recipient
                for recipient in recipient_data
                if recipient["id"] in partner_ids
            ]

        return recipient_data