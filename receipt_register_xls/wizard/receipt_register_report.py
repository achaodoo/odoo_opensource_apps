# -*- coding: utf-8 -*-
from odoo import models, fields
import base64
import io
import xlsxwriter
from odoo.exceptions import ValidationError


class ReceiptRegisterReport(models.TransientModel):
    _name = "rec.reg.report"
    _description = "Receipt Register Report"

    date_start = fields.Date('Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date('Date End', required=True, default=fields.Date.context_today)
    partner_ids = fields.Many2many('res.partner', string="Partners")
    report_file = fields.Binary(string="Report File")

    def action_generate_receipt_register_report(self):
        if self.date_end < self.date_start:
            raise ValidationError('start date should be less than end date')

        if self.partner_ids and len(self.partner_ids) >= 1:
            partner_domain = ('partner_id', 'in', self.partner_ids.ids)

        if not self.partner_ids:
            bank_cash_payments = self.env['account.payment'].search(
                [('date', '>=', self.date_start), ('date', '<=', self.date_end), ('journal_id.type', 'in', ('bank','cash')),
                 ('state', '=', 'posted'), ('payment_type', '=', 'inbound'), ('partner_id', '!=', False)] ,order="date asc, name asc")

        else:
            bank_cash_payments = self.env['account.payment'].search(
                [('date', '>=', self.date_start), ('date', '<=', self.date_end),('journal_id.type', 'in', ('bank','cash')),
                 ('state', '=', 'posted'), ('payment_type', '=', 'inbound'), partner_domain],order="date asc, name asc")

        if not bank_cash_payments:
            raise ValidationError('No datas available on these date period')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        header_format = workbook.add_format(
            {'font_size': 11, 'align': 'center', 'bold': True, 'bg_color': '#686894', 'font_color': '#FFFFFF','font_name': 'Aptos Narrow', })
        line_format_right = workbook.add_format(
            {'font_size': 11, 'align': 'right','font_name': 'Aptos Narrow',})
        line_format_left = workbook.add_format(
            {'font_size': 11, 'align': 'left','font_name': 'Aptos Narrow',})
        total_line_format_right = workbook.add_format(
            {'font_size': 11, 'align': 'right', 'bold': True, 'num_format': '#,##0.00','font_name': 'Aptos Narrow', })
        total_line_format_right.set_top()
        total_line_format_right.set_bottom(6)
        company_id = self.env.company
        header_values = [
            'Date',
            'Receipt No',
            'Customer',
            'Narration',
            'Destination Account',
            'State',
            'Amount',
        ]
        row_number = 0
        column_number = 0
        ending_range = len(header_values)
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'left',
            'valign': 'vcenter',
            'italic': True,
            'bg_color': '#83831A',
            'font_color': '#FFFFFF',
            'font_name': 'Aptos Narrow'
        })
        sheet.merge_range(row_number, column_number, row_number, ending_range - 1, company_id.name, title_format)
        row_number += 1
        sheet.merge_range(row_number, column_number, row_number, ending_range - 1,
                          "Receipt Register", title_format)
        row_number += 1
        sheet.merge_range(row_number, column_number, row_number, ending_range - 1,
                          self.date_start.strftime("%d-%m-%Y") + " To " + self.date_end.strftime("%d-%m-%Y"),
                          title_format)
        row = 4
        col = 0
        for header in header_values:
            sheet.write(row, col, header, header_format)
            col += 1
        row = 5
        col = 0
        total_amount = 0.0
        for pay in bank_cash_payments:
            sheet.write(row, col, pay.date.strftime("%d-%m-%Y") if pay.date else '', line_format_left)
            sheet.write(row, col + 1, pay.name or '', line_format_left)
            sheet.write(row, col + 2, pay.partner_id.name if pay.partner_id else '', line_format_left)
            sheet.write(row, col + 3, pay.ref or '', line_format_left)
            sheet.write(
                row, col + 4,
                pay.destination_account_id.display_name
                if pay.destination_account_id else '',
                line_format_left
            )
            sheet.write(
                row, col + 5,
                pay.partner_id.state_id.name
                if pay.partner_id and pay.partner_id.state_id else '',
                line_format_left
            )
            sheet.write(row, col + 6, "{:0.2f}".format(pay.amount_company_currency_signed), line_format_right)
            total_amount += pay.amount_company_currency_signed

            row += 1
        sheet.write(
            row, col + 5,
                 'Total ' + self.env.company.currency_id.name,
            total_line_format_right
        )
        sheet.write(
            row, col + 6,
            "{:0.2f}".format(total_amount),
            total_line_format_right
        )
        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 22)
        sheet.set_column(2, 4, 20)
        sheet.set_column(5, 6, 15)
        workbook.close()
        output.seek(0)
        file_base64 = base64.b64encode(output.read())
        self.write({'report_file': file_base64})
        return {'type': 'ir.actions.act_url',
                'url': '/web/binary/export_receipt_register_report?id=%s&model=rec.reg.report' % (
                    self.id),
                'target': 'new'}
