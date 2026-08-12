# -*- coding: utf-8 -*-
from odoo import models
import json
import re


class SummarySalesBookReport(models.AbstractModel):
    """Generate the Summary Sales Book Report in XLSX format."""

    _name = 'report.summary_sales_book_report.summary_sales_book_report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        """Generate the Summary Sales Book XLSX report."""

        sheet = workbook.add_worksheet('Summary Sales Book Report')
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter', 'italic': True,
            'bg_color': '#714B67', 'font_color': '#FFFFFF', 'font_name': 'Aptos Narrow'
        })
        left_aligned_format = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        wrap_format = workbook.add_format({'text_wrap': True})
        amount_format = workbook.add_format({'text_wrap': True, "num_format": "0.00"})
        date_from = data['form'][0]['date_from']
        date_to = data['form'][0]['date_to']
        companies = self.env.companies
        company_name = ', '.join(companies.mapped('name'))
        report_title = "Summary Sales Book"
        date_range = f"{date_from} To {date_to}"
        sheet.merge_range('A1:H1', company_name, title_format)
        sheet.merge_range('A2:H2', report_title, title_format)
        sheet.merge_range('A3:H3', date_range, title_format)
        sheet.set_row(0, 30)
        sheet.set_row(1, 25)
        sheet.set_row(2, 20)
        header_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'bg_color': '#8F8F8F', 'font_color': '#FFFFFF', 'font_name': 'Aptos Narrow',
            'align': 'center', })
        header_row = 3
        headers = [
            'Date', 'Invoice No', 'Customer', 'Sales Account',
            'Narration', 'Amount', 'VAT', 'Invoice Value'
        ]
        for col_num, header in enumerate(headers):
            sheet.write(header_row, col_num, header, header_format)
        query = """
        SELECT 
            TO_CHAR(am.invoice_date, 'DD-MM-YY') AS date,
            am.name AS invoice_no,
            rp.name AS customer,
            am.narration AS narration,
            SUM(aml.price_subtotal) AS amount,
            SUM(aml.price_total - aml.price_subtotal) AS vat,
            SUM(aml.price_total) AS invoice_value,
            COALESCE(string_agg(DISTINCT aa.name::text , E'\n'), '') AS accounts
        FROM 
            account_move am
        JOIN 
            account_move_line aml ON aml.move_id = am.id
        JOIN 
            account_account aa ON aml.account_id = aa.id
        JOIN 
            res_partner rp ON am.partner_id = rp.id
        WHERE
            am.move_type = 'out_invoice'
            AND am.invoice_date BETWEEN %s AND %s
            AND aml.move_id = am.id
            AND am.state = 'posted'
            AND aml.display_type = 'product'
            AND aa.account_type = 'income'
            AND am.company_id IN %s
        GROUP BY
            am.id, rp.id
        ORDER BY
            am.invoice_date ASC;
        """
        self.env.cr.execute(query, (date_from, date_to, tuple(companies.ids)))
        invoices = self._cr.dictfetchall()

        for row_num, row in enumerate(invoices, start=4):
            narration = re.sub(
                r"<[^>]+>",
                "",
                row["narration"] or "",
            )
            acc_name_entries = []
            for acc_entry in row['accounts'].split('\n'):
                try:
                    acc_entry_dict = json.loads(acc_entry)
                    acc_name = acc_entry_dict.get("en_US", acc_entry)
                    acc_name_entries.append(acc_name)
                except json.JSONDecodeError:
                    acc_name_entries.append(acc_entry)
            acc_name = ', '.join(acc_name_entries)
            sheet.write(row_num, 0, row['date'] or '', left_aligned_format)
            sheet.write(row_num, 1, row['invoice_no'] or '', left_aligned_format)
            sheet.write(row_num, 2, row['customer'] or '', left_aligned_format)
            sheet.write(row_num, 3, acc_name or '', wrap_format)
            sheet.write(row_num, 4, narration, left_aligned_format)
            sheet.write(row_num, 5, row['amount'] or '', amount_format)
            sheet.write(row_num, 6, row['vat'] or '', amount_format)
            sheet.write(row_num, 7, row['invoice_value'] or '', amount_format)
            row_num += 1
        sheet.set_column('A:A', 15)  # Date
        sheet.set_column('B:B', 20)  # Invoice No
        sheet.set_column('C:C', 30)  # Customer
        sheet.set_column('D:D', 25)  # Sales Account
        sheet.set_column('E:E', 50)  # Narration
        sheet.set_column('F:F', 15)  # Amount
        sheet.set_column('G:G', 10)  # VAT
        sheet.set_column('H:H', 20)  # Invoice Value