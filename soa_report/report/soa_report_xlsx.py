# -*- coding: utf-8 -*-
from odoo import  models
from datetime import datetime


class SoaReportXlsx(models.AbstractModel):
    _name = 'report.soa_report.soa_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def _get_excel_report_values(self, data):
        partner_id = data['form'][0]['partner_id'][0] if isinstance(data['form'][0]['partner_id'], (list, tuple)) else \
            data['form'][0]['partner_id']
        as_on_date_str = data['form'][0]['as_on_date']
        as_on_date = datetime.strptime(as_on_date_str, '%Y-%m-%d').date()
        payment_entries = []
        partner_rec = self.env['res.partner'].browse(partner_id)
        if not partner_rec:
            return
        # 1. Fetch and process payments
        payment_rec = self.env['account.payment'].search([
            ('partner_id', '=', partner_id),
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound'),
            ('date', '<=', as_on_date)
        ])
        # Collect all credit move lines from payment journal entries
        credit_lines = payment_rec.mapped('move_id.line_ids').filtered(lambda l: l.credit)
        partial_recs = self.env['account.partial.reconcile'].search([
            ('credit_move_id', 'in', credit_lines.ids)
        ])
        # Group partial reconciles by credit move line
        partials_by_credit_line = {}
        for part in partial_recs:
            partials_by_credit_line.setdefault(part.credit_move_id.id, []).append(part)
        # Process each payment move line
        for line in credit_lines:
            part_list = partials_by_credit_line.get(line.id, [])
            payment_bal = line.credit
            for part in part_list:
                if part.max_date <= as_on_date:
                    payment_bal -= part.debit_amount_currency
            if not part_list or payment_bal > 0:
                payment_entries.append({
                    'invoice_date': line.date.strftime('%d-%m-%Y'),
                    'voucher': line.move_id.name,
                    'narration': line.move_id.payment_reference or '',
                    'credit_days': line.partner_id.property_payment_term_id.name,
                    'expected_date': line.date,
                    'balance': payment_bal if payment_bal else line.credit,
                    'move_type': 'out_refund'
                })
        # 2. Process invoices
        invoice_rec = self.env['account.move'].search([
            ('partner_id', '=', partner_id),
            ('state', '=', 'posted'),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('invoice_date', '<=', as_on_date)
        ])
        all_invoice_lines = invoice_rec.mapped('line_ids')
        partial_recs_invoice = self.env['account.partial.reconcile'].search([
            '|',
            ('debit_move_id', 'in', all_invoice_lines.ids),
            ('credit_move_id', 'in', all_invoice_lines.ids)
        ])
        # Organize partials by move line
        partials_by_line = {}
        for part in partial_recs_invoice:
            if part.debit_move_id:
                partials_by_line.setdefault(part.debit_move_id.id, []).append(part)
            if part.credit_move_id:
                partials_by_line.setdefault(part.credit_move_id.id, []).append(part)
        # Adjust totals based on partial reconciliations
        for inv in invoice_rec:
            inv_total = inv.amount_total
            for line in inv.line_ids:
                partials = partials_by_line.get(line.id, [])
                for part in partials:
                    if part.max_date <= as_on_date:
                        if inv.move_type == 'out_refund':
                            inv_total -= part.credit_amount_currency
                        else:
                            inv_total -= part.debit_amount_currency
            if inv_total:
                payment_entries.append({
                    'invoice_date': inv.invoice_date.strftime('%d-%m-%Y'),
                    'voucher': inv.name,
                    'narration': inv.payment_reference or '',
                    'credit_days': inv.partner_id.property_payment_term_id.name,
                    'expected_date': inv.invoice_date,
                    'balance': inv_total,
                    'move_type': 'out_refund' if inv.move_type == 'out_refund' else 'out_invoice'
                })
        # 3. Process journal entries
        journal_entry_lines = self.env['account.move.line'].search([
            ('partner_id', '=', partner_id),
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', '=', 'entry'),
            ('move_id.date', '<=', as_on_date),
            ('account_id.account_type', '=', 'asset_receivable'),
            ('move_id.payment_id', '=', False)
        ])
        # Add journal entries to payment entries
        for entry in journal_entry_lines:
            payment_entries.append({
                'invoice_date': entry.move_id.date.strftime('%d-%m-%Y'),
                'voucher': entry.move_id.name,
                'narration': entry.move_id.payment_reference or '',
                'credit_days': entry.partner_id.property_payment_term_id.name,
                'expected_date': entry.move_id.date,
                'balance': entry.credit or entry.debit,
                'move_type': 'out_refund' if entry.credit else 'out_invoice'
            })
        # Final result
        customer_invoices = payment_entries
        total_balance = total_30 = total_30_60 = total_60_90 = total_90_180 = total_180_360 = total_greater_360 = 0.0
        invoices_data = []
        for row in customer_invoices:
            credit_days = row['credit_days'] if isinstance(row['credit_days'], str) else ''
            balance = row['balance'] or 0.0 if row['move_type'] == 'out_invoice' else -row['balance'] or 0.0
            expected_date = row.get('expected_date')
            invoice_date = row.get('invoice_date')
            invoice_date_obj = datetime.strptime(invoice_date, '%d-%m-%Y').date()
            days_diff = (as_on_date - invoice_date_obj).days if invoice_date else 0
            under_30 = between_30_60 = between_60_90 = between_90_180 = between_180_360 = greater_360 = 0.0
            if 1 <= days_diff <= 30:
                under_30 = balance
            elif 31 <= days_diff <= 60:
                between_30_60 = balance
            elif 61 <= days_diff <= 90:
                between_60_90 = balance
            elif 91 <= days_diff <= 180:
                between_90_180 = balance
            elif 181 <= days_diff <= 360:
                between_180_360 = balance
            elif days_diff > 360:
                greater_360 = balance
            total_balance += balance
            total_30 += under_30
            total_30_60 += between_30_60
            total_60_90 += between_60_90
            total_90_180 += between_90_180
            total_180_360 += between_180_360
            total_greater_360 += greater_360
            invoices_data.append({
                'voucher': row['voucher'],
                'invoice_date': row['invoice_date'],
                'narration': row['narration'],
                'credit_days': credit_days,
                'expected_date': expected_date,
                'balance': balance,
                'under_30': under_30,
                'between_30_60': between_30_60,
                'between_60_90': between_60_90,
                'between_90_180': between_90_180,
                'between_180_360': between_180_360,
                'greater_360': greater_360
            })
        return invoices_data

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('SOA Report')
        header_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'bg_color': '#D3D3D3', 'font_color': 'black', 'font_name': 'Arial',
            'align': 'center', 'underline': True
        })
        clm_header_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'bg_color': '#D3D3D3', 'font_color': 'black', 'font_name': 'Arial',
            'align': 'center', 'valign': 'bottom', 'border': 1, 'bottom': 1
        })
        partner_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'bg_color': '#D3D3D3', 'font_color': 'black', 'font_name': 'Arial',
            'align': 'left', 'valign': 'left', 'border': 0, 'text_wrap': True
        })
        company_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'bg_color': '#D3D3D3', 'font_color': 'black', 'font_name': 'Arial',
            'align': 'left', 'valign': 'vcenter', 'border': 0, 'text_wrap': True
        })
        right_aligned_format = workbook.add_format(
            {'num_format': '#,##0.00', 'align': 'right', 'valign': 'vcenter', 'border': 1})
        total_aligned_format = workbook.add_format(
            {'num_format': '#,##0.00', 'align': 'right', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D3D3D3',
             'bold': True})
        left_aligned_format = workbook.add_format({'align': 'left', 'valign': 'top', 'border': 1, 'text_wrap': True})
        total_head_format = workbook.add_format({'align': 'center', 'bg_color': '#D3D3D3', 'border': 0, 'bold': True})
        partner_id = data['form'][0].get('partner_id')[0] if data['form'][0].get('partner_id') else None
        as_on_date_str = data['form'][0]['as_on_date']
        as_on_date = datetime.strptime(as_on_date_str, '%Y-%m-%d').date()
        as_on_date_1 = as_on_date.strftime('%d/%m/%Y')
        if partner_id:
            report_title = f"""SOA Report As On {as_on_date_1}"""
            partner = self.env['res.partner'].search([('id', '=', partner_id)])
            partner_details = f"""
            {partner.name}
            PO Box: {partner.zip or 'N/A'}{', ' + partner.street if partner.street else ''}
            {partner.street2 if partner.street2 else ''}{', ' + partner.city if partner.city else ''},
            {partner.state_id.name if partner.state_id else ''}{', ' + partner.country_id.name if partner.country_id else ''}
            Tel: {partner.phone or 'N/A'}
            """
            company = self.env.company
            tmax_details = f"""
            {company.name}
            PO Box: {company.zip or 'N/A'}, Office No: {company.street or ''}{',' if company.street else ''}
            {company.street2 or ''}{',' if company.street2 else ''} {company.city or ''}, {company.state_id.name or ''}, {company.country_id.name or ''}
            Tel: {company.phone or 'N/A'}
            """
            sheet.merge_range('A1:K1', report_title, header_format)
            sheet.merge_range('A2:F2', partner_details, partner_format)
            sheet.merge_range('G2:K2', tmax_details, company_format)
            sheet.write('D2', "", partner_format)
            # Adjusting row height for better visibility
            sheet.set_row(1, 130)
            sheet.set_row(2, 50)
            header_row = 2
            headers = ['Voucher No.', 'Date', 'Narration', 'Credit Days', 'Balance', '1-30', '31-60', '61-90',
                       '91-180', '181-360', '>360']
            report_data = self._get_excel_report_values(data)
            for col_num, header in enumerate(headers):
                if col_num != 2:
                    sheet.set_column(col_num, col_num, 20)
                sheet.write(header_row, col_num, header, clm_header_format)
            header_row += 1
            total_balance = between_90_180 = between_180_360 = under_30 = between_30_60 = between_60_90 = greater_360 = 0
            for line in report_data:
                sheet.write(header_row, 0, line['voucher'], left_aligned_format)
                sheet.write(header_row, 1, line['invoice_date'], right_aligned_format)
                sheet.write(header_row, 2, line['narration'], left_aligned_format)
                sheet.write(header_row, 3, line['credit_days'], right_aligned_format)
                sheet.write(header_row, 4, line['balance'], right_aligned_format)
                sheet.write(header_row, 5, line['under_30'], right_aligned_format)
                sheet.write(header_row, 6, line['between_30_60'], right_aligned_format)
                sheet.write(header_row, 7, line['between_60_90'], right_aligned_format)
                sheet.write(header_row, 8, line['between_90_180'], right_aligned_format)
                sheet.write(header_row, 9, line['between_180_360'], right_aligned_format)
                sheet.write(header_row, 10, line['greater_360'], right_aligned_format)
                header_row += 1
                total_balance += line['balance']
                under_30 += line['under_30']
                between_30_60 += line['between_30_60']
                between_60_90 += line['between_60_90']
                between_90_180 += line['between_90_180']
                between_180_360 += line['between_180_360']
                greater_360 += line['greater_360']
            sheet.write(header_row, 0, '', total_head_format)
            sheet.write(header_row, 1, '', total_head_format)
            sheet.write(header_row, 2, '', total_head_format)
            sheet.write(header_row, 3, 'Total', total_head_format)
            sheet.write(header_row, 4, total_balance, total_aligned_format)
            sheet.write(header_row, 5, under_30, total_aligned_format)
            sheet.write(header_row, 6, between_30_60, total_aligned_format)
            sheet.write(header_row, 7, between_60_90, total_aligned_format)
            sheet.write(header_row, 8, between_90_180, total_aligned_format)
            sheet.write(header_row, 9, between_180_360, total_aligned_format)
            sheet.write(header_row, 10, greater_360, total_aligned_format)
            sheet.set_column('C:C', 50)
