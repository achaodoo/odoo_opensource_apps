# -*- coding: utf-8 -*-
from odoo import fields, models

class SaleReport(models.Model):
    _inherit = "sale.report"

    commitment_date = fields.Datetime("Delivery Date", readonly=True)


    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['commitment_date'] = "s.commitment_date"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += """,
            s.commitment_date"""
        return res