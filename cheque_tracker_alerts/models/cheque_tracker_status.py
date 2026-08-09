# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ChequeTrackerStatus(models.Model):
    """Manage cheque tracker statuses and their alert configuration.
    This model defines PDC and CDC cheque statuses and configures whether
    an alert is required and how many days before the cheque date the alert
    should be triggered.
    """

    _name = 'cheque.tracker.status'
    _description = 'Cheque Tracker Status '
    _rec_name = 'cheque_tracker_name'

    name = fields.Selection([('pdc', 'PDC'), ('cdc', 'CDC')], string='Status')
    alert_required = fields.Selection([('yes', 'Yes'), ('no', 'NO'), ], string='Alert Required')
    no_of_days = fields.Integer(string="Number of Days")
    is_completed = fields.Boolean(string="Completed")
    cheque_tracker_name = fields.Char()

    @api.onchange('name')
    def _onchange_name(self):
        """Update the tracker name based on the selected status.
        Uses the display label of the selected ``name`` value to populate the
        ``cheque_tracker_name`` field.
        """
        for rec in self:
            if rec.name:
                tracker_name = dict(self._fields['name']._description_selection(self.env)).get(rec.name)
                rec.cheque_tracker_name = tracker_name
