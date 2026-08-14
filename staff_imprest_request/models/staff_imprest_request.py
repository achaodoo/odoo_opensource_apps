# -*- coding: utf-8 -*-

from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError


class StaffImprestRequest(models.Model):
    _name = 'staff.imprest.request'
    _description = 'Staff Imprest Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    def _get_default_groups(self):
        return [Command.link(self.env.ref('base.group_user').id)]

    def _get_default_journal(self):
        journal = self.env['account.journal'].search([('is_staff_imprest_journal', '=', True), ('type', 'in', ['cash', 'bank']), ('company_id', '=', self.env.company.id)], limit=1)
        if journal:
            return journal.id
        else:
            return False

    name = fields.Char('Name', required=True, copy=False, readonly=False, index='trigram',
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee ID', required=True,
                                  domain="[('company_id', '=', company_id),]", default=lambda self: self.env.user.employee_id)
    description = fields.Char("Description", required=True)
    date = fields.Date(default=lambda self: fields.Date.today(), required=True)
    status = fields.Selection([('new', 'New'), ('hod_approval', 'HOD Approval'),
                               ('finance_mgr_approval', 'Finance Manager Approval'),
                               ('closed', 'Closed'), ('reject', 'Rejected')], default='new', tracking=True)
    assigned_user_ids = fields.Many2many(
        'res.users', string='Assigned User', default=lambda self: self.env.user, tracking=True)
    is_self_assigned_user = fields.Boolean(compute="_compute_is_self_assigned_user")
    assigned_group_ids = fields.Many2many('res.groups', string="Assigned Role", default=_get_default_groups)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        string='Company Currency', related='company_id.currency_id', readonly=True)
    is_self_assign = fields.Boolean(string="Self Assign", default=False)
    reject_reason = fields.Char(string="Reject Reason")
    is_department_head = fields.Boolean(compute="_compute_is_department_head")
    amount = fields.Monetary(string="Amount", tracking=True, required=True)
    user_id = fields.Many2one('res.users', string="Requested By", default=lambda self: self.env.user, required=True, tracking=True)
    account_journal_id = fields.Many2one(
        'account.journal', default=_get_default_journal, required=True,
        domain="[('is_staff_imprest_journal', '=', True), ('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]")
    approval_hod_id = fields.Many2one('res.users', string="Approval HOD")
    approval_finance_id = fields.Many2one('res.users', string="Approval Finance")
    payment_id = fields.Many2one('account.payment', string="Payment")

    def _compute_is_department_head(self):
        for record in self:
            if (
                    self.env.user.id in record.employee_id.department_id.department_head_ids.user_id.ids and self.env.user.id in record.assigned_user_ids.ids) or self.env.user.has_group(
                    'base.group_system'):
                record.is_department_head = True
            else:
                record.is_department_head = False

    def _compute_is_self_assigned_user(self):
        for record in self:
            if self.env.user.id in record.assigned_user_ids.ids or self.env.user.has_group('base.group_system'):
                record.is_self_assigned_user = True
            else:
                record.is_self_assigned_user = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            employee_id = vals.get('employee_id')

            if not employee_id:
                raise UserError(_("Please select an employee."))

            employee = self.env['hr.employee'].browse(employee_id)

            if not employee.department_id:
                raise UserError(_("Please assign a department to the employee."))

            if vals.get('company_id'):
                self = self.with_company(vals['company_id'])

            if vals.get('name', _("New")) == _("New"):
                vals['name'] = (
                        self.env['ir.sequence'].next_by_code('staff.imprest.request')
                        or _("New")
                )

        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.status != 'new':
                raise UserError(_("You can't delete request after submission"))
        return super().unlink()

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_("Amount must be greater than zero."))

    def action_submit(self):
        for record in self:
            if self.env.user != record.user_id:
                raise ValidationError(
                    _("You don't have access to submit this request.")
                )

            hod_group = self.env.ref(
                'staff_imprest_request.group_staff_imprest_hod',
                raise_if_not_found=False,
            )
            hod_users = hod_group.users if hod_group else self.env['res.users']

            if not hod_users:
                raise ValidationError(
                    _("Please assign at least one user to the Staff Imprest HOD group.")
                )

            email_template = self.env.ref(
                'staff_imprest_request.email_template_staff_imprest_hod_approval',
                raise_if_not_found=False,
            )

            hod_emails = hod_users.mapped('partner_id.email')
            hod_emails = [email for email in hod_emails if email]

            if email_template and hod_emails and self.env.user.partner_id.email:
                email_values = {
                    'email_to': ','.join(hod_emails),
                    'email_from': self.env.user.partner_id.email,
                }
                email_template.send_mail(
                    record.id,
                    email_values=email_values,
                    force_send=True,
                )

            record.assigned_user_ids = [
                Command.link(user.id) for user in hod_users
            ]
            record.assigned_group_ids = False
            record.status = 'hod_approval'

    def action_self_assign(self):
        for record in self:
            if record.is_self_assign:
                continue

            if record.status == 'hod_approval':
                if (
                        self.env.user in record.assigned_user_ids
                        or self.user_has_groups('base.group_system')
                ):
                    record.write({
                        'is_self_assign': True,
                        'approval_hod_id': self.env.user.id,
                    })

                    record.assigned_group_ids = False
                    record.assigned_user_ids = False

                    record.sudo().assigned_user_ids = [
                        Command.link(self.env.user.id)
                    ]

                else:
                    raise ValidationError(
                        _("You don't have access to self assign this imprest request.")
                    )

            elif record.status == 'finance_mgr_approval':
                if (
                        self.env.user in record.assigned_user_ids
                        or self.user_has_groups('base.group_system')
                ):
                    record.write({
                        'is_self_assign': True,
                        'approval_finance_id': self.env.user.id,
                    })

                    record.assigned_group_ids = False
                    record.assigned_user_ids = False

                    record.sudo().assigned_user_ids = [
                        Command.link(self.env.user.id)
                    ]

                else:
                    raise ValidationError(
                        _("You don't have access to self assign this imprest request.")
                    )

    def action_approve(self):
        for record in self:
            current_user = self.env.user

            if record.status == 'hod_approval':
                if (
                        current_user != record.approval_hod_id
                        and not current_user.has_group('base.group_system')
                ):
                    raise ValidationError(
                        _("You don't have access to approve this imprest request.")
                    )

                record.status = 'finance_mgr_approval'

                finance_group = self.env.ref(
                    'staff_imprest_request.group_staff_imprest_finance'
                )
                finance_users = finance_group.users

                record.assigned_group_ids = [
                    Command.link(finance_group.id)
                ]

                email_template = self.env.ref(
                    'staff_imprest_request.email_template_finance_manager_approval',
                    raise_if_not_found=False,
                )

                finance_emails = finance_users.mapped('partner_id.email')
                finance_emails = [
                    email for email in finance_emails if email
                ]

                if (
                        email_template
                        and finance_emails
                        and record.approval_hod_id.partner_id.email
                ):
                    email_values = {
                        'email_to': ','.join(finance_emails),
                        'email_from': record.approval_hod_id.partner_id.email,
                    }
                    email_template.send_mail(
                        record.id,
                        email_values=email_values,
                        force_send=True,
                    )

                record.is_self_assign = False
                record.assigned_user_ids = [
                    Command.link(user.id)
                    for user in finance_users
                ]

            elif record.status == 'finance_mgr_approval':
                if (
                        current_user != record.approval_finance_id
                        and not current_user.has_group('base.group_system')
                ):
                    raise ValidationError(
                        _("You don't have access to approve this imprest request.")
                    )

                finance_group = self.env.ref(
                    'staff_imprest_request.group_staff_imprest_finance'
                )
                finance_users = finance_group.users

                email_template = self.env.ref(
                    'staff_imprest_request.email_template_imprest_approved_by_finance_manager',
                    raise_if_not_found=False,
                )

                email_to = finance_users.mapped('partner_id.email')
                email_to = [email for email in email_to if email]

                if (
                        email_template
                        and email_to
                        and record.approval_finance_id.partner_id.email
                ):
                    email_values = {
                        'email_to': ','.join(email_to),
                        'email_from': record.approval_finance_id.partner_id.email,
                    }
                    email_template.send_mail(
                        record.id,
                        email_values=email_values,
                        force_send=True,
                    )

                account_payment = self.env['account.payment'].create({
                    'payment_type': 'outbound',
                    'journal_id': record.account_journal_id.id,
                    'partner_id': record.user_id.partner_id.id,
                    'partner_type': 'supplier',
                    'amount': record.amount,
                    'currency_id': record.currency_id.id,
                    'ref': record.name,
                })

                account_payment.action_post()

                record.payment_id = account_payment.id
                record.status = 'closed'

            if (
                    current_user not in record.sudo().assigned_user_ids
                    and not current_user.has_group('base.group_system')
            ):
                return {
                    'name': _('Staff Imprest Request'),
                    'view_mode': 'tree,form',
                    'res_model': 'staff.imprest.request',
                    'type': 'ir.actions.act_window',
                    'target': 'main',
                }

    def action_open_account_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'name': _('Imprest Payment'),
            'view_mode': 'form',
            'res_id': self.payment_id.id,
            'context': dict(self._context, create=False),
        }

    def action_reject(self):
        self.ensure_one()
        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'staff.imprest.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }