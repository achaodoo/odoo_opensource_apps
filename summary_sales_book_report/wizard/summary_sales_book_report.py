# -*- coding: utf-8 -*-
from odoo import fields,models


class SummarySalesBookReport(models.TransientModel):
    """Provide a wizard to generate the Summary Sales Book Report."""

    _name = "summary.sales.book.report"
    _description = "Summary Sales Book Report "

    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)

    def action_generate_report(self):
        """Generate the Summary Sales Book XLSX report."""

        self.ensure_one()
        data = self.read()
        data = {
            'form': data,
        }
        return self.env.ref(
            'summary_sales_book_report.action_summary_sales_book_report_xlsx').sudo().report_action(self, data=data)


