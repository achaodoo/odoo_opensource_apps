# -*- coding: utf-8 -*-
from odoo import fields, models, _, Command
from odoo.exceptions import ValidationError, UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"
    _inherits = {'account.move': 'move_id'}

    def _compute_is_approve_person(self):
        approver_group = self.env.ref('vendor_payment_approval.group_vendor_payment_approver')
        approver_users = self.env['res.users'].search([('groups_id', 'in', approver_group.id),('company_ids', 'in', self.company_id.id)])
        assigned_user_ids = [user.id for user in approver_users]
        for rec in self:
            if rec.payment_type == 'outbound':
                rec.is_approve_person = True if (self.env.user.id in assigned_user_ids) or self.env.user.has_group(
                    'base.group_system') else False
            else:
                rec.is_approve_person = False

    def _get_default_groups(self):
        return [Command.link(self.env.ref('base.group_user').id)]

    is_approve_person = fields.Boolean(string='Approving Person',
                                       compute=_compute_is_approve_person,
                                       readonly=True,
                                       help="Enable/disable if approving"
                                            " person.")

    reject_reason = fields.Char(string="Reject Reason")
    is_vendor_approval = fields.Boolean(string="Vendor Approval", copy=False)
    account_invoice_line = fields.Many2one('account.move.line', string='Account Invoice line', ondelete='cascade')
    approval_finance_id = fields.Many2one('res.users', string="Approval Finance", copy=False)
    is_self_assign = fields.Boolean(string="Self Assign", copy=False, default=False)
    assigned_user_ids = fields.Many2many(
        'res.users', string='Assigned User', default=lambda self: self.env.user, tracking=True)
    assigned_group_ids = fields.Many2many('res.groups', string="Assigned Role", default=_get_default_groups)

    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill')
    is_logged_user = fields.Boolean(default=False, compute='_compute_is_logged_user', copy=False)

    is_fin_mngr_required = fields.Boolean(default=False, copy=False)
    amount = fields.Monetary(currency_field='currency_id', copy=False) # Prevents amount from being copied when duplicating a record


    def _compute_is_logged_user(self):
        for record in self:
            if self.env.user.has_group('base.group_system'):
                record.is_logged_user = True
            elif record.approval_finance_id:
                record.is_logged_user = (record.approval_finance_id == self.env.user)
            else:
                record.is_logged_user = False

    def action_self_assign(self):
        """Assign the payment approval to the current user.

        The current user must belong to the Vendor Payment Approver group.
        """
        approver_group = self.env.ref(
            'vendor_payment_approval.group_vendor_payment_approver'
        )

        approver_users = self.env['res.users'].search([
            ('groups_id', 'in', approver_group.id),
            ('company_ids', 'in', self.company_id.ids),
        ])

        for rec in self:
            if rec.state not in ('waiting_approval', 'approved'):
                continue

            rec.assigned_user_ids = [
                Command.unlink(user.id)
                for user in approver_users
            ]

            rec.assigned_user_ids = [
                Command.link(self.env.user.id)
            ]

            rec.write({
                'is_self_assign': True,
                'approval_finance_id': self.env.user.id,
            })

    def action_post(self):
        for rec in self:
            if rec.state == "draft" and rec.payment_type == 'outbound':
                validation = self._check_payment_approval()
                if validation:
                    if rec.state == (
                            'posted', 'cancel', 'waiting_approval', 'rejected'):
                        raise UserError(
                            _("Only a draft or approved payment can be posted."))
                    if any(inv.state != 'posted' for inv in
                           rec.reconciled_invoice_ids):
                        raise ValidationError(_("The payment cannot be processed "
                                                "because the invoice is not open!"))
                    rec.move_id._post(soft=False)
            elif rec.is_vendor_approval == True and rec.state != "draft" and rec.payment_type == 'outbound':
                super().action_post()
                domain = [
                    ('parent_state', '=', 'posted'),
                    ('account_type', 'in', self.env['account.payment']._get_valid_payment_account_types()),
                    ('reconciled', '=', False),
                ]
                payment_lines = self.line_ids.filtered_domain(domain)
                # lines = self.line_ids.filtered(lambda e: e.account_type == 'liability_payable')
                lines = self.account_invoice_line

                for account in payment_lines.account_id:
                    (payment_lines + lines) \
                        .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                        .reconcile()
            else:
                return super().action_post()

    def _check_payment_approval(self):
        for rec in self:
            if rec.state == "draft" and rec.payment_type == 'outbound' and 'expense_sheet_register_payment' not in self.env.context:
                rec.move_id.write({
                    'state': 'waiting_approval',
                    'is_register_payment': True
                })
                rec.write({
                    'state': 'waiting_approval',
                    'is_self_assign': False
                })
                return False
        return True

    def approve_transfer(self):
        for rec in self:
            email_template = self.env.ref(
                'vendor_payment_approval.email_vendor_payment_accountant_notification',
                raise_if_not_found=False
            )
            if not email_template:
                raise ValidationError(
                    'Email template not found. Cannot proceed.'
                )

            approver_group = self.env.ref(
                'vendor_payment_approval.group_vendor_payment_approver'
            )

            approver_users = self.env['res.users'].search([
                ('groups_id', 'in', approver_group.id),
                ('company_ids', 'in', rec.company_id.id),
            ])

            approver_emails = [
                user.email for user in approver_users if user.email
            ]

            if not approver_emails:
                raise ValidationError(
                    'No user emails found for the Vendor Payment Approver group.'
                )

            email_values = {
                'email_to': ','.join(approver_emails)
            }

            email_template.with_context(email_values).send_mail(
                rec.id,
                force_send=True,
                email_values=email_values,
            )

            if rec.is_approve_person:
                rec.move_id.write({
                    'state': 'approved'
                })

                rec.write({
                    'state': 'approved',
                    'is_self_assign': False,
                    'assigned_user_ids': [(6, 0, approver_users.ids)],
                    'assigned_group_ids': [(6, 0, approver_group.ids)],
                })

            return True

    def reject_transfer(self):
        """Open the rejection reason wizard."""
        self.ensure_one()

        return {
            "name": "Reject Vendor Payment",
            "type": "ir.actions.act_window",
            "res_model": "vendor.payment.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
                "active_model": "account.payment",
            },
        }

    def action_send_approval_email(self):
        for record in self:
            approver_group = self.env.ref('vendor_payment_approval.group_vendor_payment_approver')
            approver_users = self.env["res.users"].search([
                ("groups_id", "in", approver_group.id),
                ("company_ids", "in", record.company_id.id),
            ])
            approver_emails = [manager.email for manager in approver_users if manager.email]
            email_template = self.env.ref('vendor_payment_approval.email_vendor_payment_approval_notification',
                                          raise_if_not_found=False)
            if not email_template:
                raise ValidationError(
                    'Email template not found')
            if approver_emails:
                email_values = {'email_to': ','.join(approver_emails)}
                email_template.with_context(email_values).send_mail(record.id, force_send=True)
                return True
            else:
                raise ValidationError(
                    'No email addresses are available for the Vendor Payment Approver group.')

    def action_send_for_approval(self):
        for record in self:
            approver_group = self.env.ref('vendor_payment_approval.group_vendor_payment_approver')
            approver_users = self.env['res.users'].search([('groups_id', '=', approver_group.id),('company_ids', 'in', record.company_id.id)])
            if not approver_users:
                raise ValidationError(
                    "No users are assigned to the Vendor Payment Approver group."
                )
            if record.payment_type == 'outbound' and record.state == 'draft':
                record.sudo().write({
                    'assigned_user_ids': [(6, 0, approver_users.ids)],
                    'assigned_group_ids': [(6, 0, approver_group.ids)],
                    'state': 'waiting_approval',
                })
                record.action_send_approval_email()




