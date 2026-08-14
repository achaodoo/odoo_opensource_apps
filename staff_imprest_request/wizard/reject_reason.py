from odoo import _, fields, models
from odoo.exceptions import ValidationError


class StaffImprestRejectWizard(models.TransientModel):
    _name = 'staff.imprest.reject.wizard'
    _description = 'Staff Imprest Request Rejection'

    reason = fields.Text(
        string='Reason',
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()

        active_id = self.env.context.get('active_id')
        if not active_id:
            raise ValidationError(
                _("No Staff Imprest Request was selected.")
            )

        imprest = self.env['staff.imprest.request'].browse(active_id)

        if not imprest.exists():
            raise ValidationError(
                _("The Staff Imprest Request no longer exists.")
            )

        imprest.sudo().write({
            'reject_reason': self.reason,
            'status': 'reject',
        })

        template = self.env.ref(
            'staff_imprest_request.email_template_imprest_request_rejection',
            raise_if_not_found=False,
        )

        if template:
            template.send_mail(
                imprest.id,
                force_send=True,
            )

        return {'type': 'ir.actions.act_window_close'}