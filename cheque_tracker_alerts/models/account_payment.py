# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from datetime import  date, timedelta


class AccountPayment(models.Model):
    """Extend account payments with cheque tracking functionality.
    This model adds cheque details, tracker status, alert configuration,
    and automated email notifications for cheque payments.
    """

    _inherit = "account.payment"

    cheque_date = fields.Date(string="Cheque Date")

    cheque_tracker_status_id = fields.Many2one(
        'cheque.tracker.status',
        string="Cheque Tracker",
        domain=[('name', 'in', ['pdc', 'cdc'])]
    )

    is_mail_sent = fields.Boolean("Send Mail")
    alert_required = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Alert Required'
    )
    is_check_tracker = fields.Boolean("Check Tracker")
    is_cheque = fields.Boolean(string='Cheque')

    @api.onchange('journal_id')
    def _onchange_journal_id_is_cheque(self):
        """Update the cheque flag based on the selected journal.
        Sets ``is_cheque`` to True when the selected journal is configured
        as a cheque journal; otherwise, it sets the value to False.
        """
        for rec in self:
            if rec.journal_id and rec.journal_id.is_cheque:
                rec.is_cheque = True
            else:
                rec.is_cheque = False

    @api.onchange('cheque_tracker_status_id')
    def _onchange_cheque_tracker_status_id(self):
        """Update the alert requirement from the tracker status. 
        When a cheque tracker status is selected, the payment's 
        ``alert_required`` field is updated with the corresponding value
        from the selected tracker status.
        """
        for rec in self:
            if rec.cheque_tracker_status_id:
                rec.alert_required = rec.cheque_tracker_status_id.alert_required

    def action_send_email_cheque_tracker(self):
        """Send cheque tracker alert emails when they are due. 
        Finds cheque payments that require an alert and have not already 
        received an email notification. The payment is marked for tracking 
        when the configured alert period is reached, and an email is sent
        to accounting users and managers.
        """
        payments = self.env['account.payment'].sudo().search([
            ('cheque_tracker_status_id', '!=', False),
            ('alert_required', '=', 'yes'),
            ('is_mail_sent', '=', False),
            ('date', '!=', False),
        ])
        date_now = date.today()
        for rec in payments:
            if rec.date and rec.cheque_tracker_status_id:
                date_before_2_days = rec.date - timedelta(rec.cheque_tracker_status_id.no_of_days)
                if date_now >= date_before_2_days and rec.alert_required == 'yes':
                    rec.is_check_tracker = True
                    if rec.is_mail_sent == False:
                        account_user = self.env.ref('account.group_account_user')
                        account_manager = self.env.ref('account.group_account_manager')
                        account_manager_users = self.env['res.users'].search(
                            [('groups_id', 'in', [account_user.id, account_manager.id])])
                        email_template = self.env.ref('cheque_tracker_alerts.email_template_check_tracker_status')
                        account_manager_emails = [manager.email for manager in account_manager_users if manager.email]
                        if account_manager_emails:
                            email_values = {'email_to': ','.join(account_manager_emails)}
                            email_template.with_context(email_values).send_mail(rec.id, force_send=True,
                                                                                email_values=email_values)
                            rec.is_mail_sent = True
                else:
                    rec.is_check_tracker = False

    @api.onchange('cheque_date')
    def _onchange_cheque_date(self):
        """Update the tracker status according to the cheque date.
        A cheque dated today or earlier is assigned a tracker status where
        alerts are not required. A future-dated cheque is assigned a tracker
        status where alerts are required.
        """
        status_obj = self.env['cheque.tracker.status']
        status_no = status_obj.search([('alert_required', '=', 'no')], limit=1)
        status_yes = status_obj.search([('alert_required', '=', 'yes')], limit=1)
        print("status_no",status_no)
        print("status_yes",status_yes)
        today = fields.Date.today()
        for rec in self:
            if not rec.cheque_date:
                continue
            rec.cheque_tracker_status_id = (
                status_no.id if rec.cheque_date <= today else status_yes.id
            )
