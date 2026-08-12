# -*- coding: utf-8 -*-
import base64
from odoo import models, fields
from datetime import datetime, date


class SOAReport(models.TransientModel):
    _name = "soa.report"
    _description = "soa Report"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Customer', domain="[('customer_rank','>',0)]")
    as_on_date = fields.Date("As On Date")

    def action_generate_pdf(self):
        data = {'partner_id': self.partner_id.id, 'as_on_date': self.as_on_date}
        return self.env.ref("soa_report.action_soa_pdf_report").report_action(self, data=data)

    def action_generate_xlsx_report(self):
        self.ensure_one()
        data = self.read()
        data = {
            'form': data,
        }
        return self.env.ref(
            'soa_report.action_soa_report_xlsx').sudo().report_action(self, data=data)

    def submit_soa_report(self):
        template_id = self.env.ref('soa_report.email_template_statement_of_account', raise_if_not_found=False)
        if template_id:
            partner_id = self.partner_id.id if self.partner_id else None
            as_on_date = self.as_on_date if self.as_on_date else None
            as_on_date_str = as_on_date.strftime('%d/%m/%Y')
            partner_name = self.partner_id.name if partner_id else "Customer"
            partner = self.env['res.partner'].browse(partner_id) if partner_id else None
            partner_credit = partner.property_payment_term_id.name if partner else None
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
                ('move_id.payment_id', '=', False),
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
                    'greater_360': greater_360,
                })
            data_report = {
                'partner_credit': partner_credit,
                'partner_name': partner_name,
                'as_on_date': as_on_date,
                'as_on_date_str': as_on_date_str,
                'invoices': invoices_data,
                'total_balance': total_balance,
                'total_30': total_30,
                'total_30_60': total_30_60,
                'total_60_90': total_60_90,
                'total_90_180': total_90_180,
                'total_180_360': total_180_360,
                'total_greater_360': total_greater_360,
                'partner_zip': partner.zip,
                'partner_street': partner.street,
                'partner_street2': partner.street2,
                'partner_city': partner.city,
                'partner_state': partner.state_id.name,
                'partner_country': partner.country_id.name,
                'partner_phone': partner.phone,
            }
            pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'soa_report.action_soa_pdf_report_mail', [self.id], data=data_report
            )
            attachment = self.env['ir.attachment'].create({
                'name': f"Statement_of_Account_{self.partner_id.name}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'soa.report',
                'res_id': self.id,
                'mimetype': 'application/pdf'
            })
            template = self.env['mail.template'].browse(template_id.id)
            ctx = {
                'default_model': 'soa.report',
                'default_res_ids': self.ids,
                'default_template_id': template.id if template else None,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
                'force_email': True,
                'default_attachment_ids': [(6, 0, [attachment.id])],
                'partner_name': partner_name,
                'total_balance': "{:,.2f}".format(total_balance),
            }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }


class SOAReportPDF(models.AbstractModel):
    _name = "report.soa_report.soa_pdf_report"
    _description = "SOA Report PDF"

    def _get_report_values(self, docids, data=None):
        partner_id = data['partner_id'][0] if isinstance(data['partner_id'], (list, tuple)) else data['partner_id']
        as_on_date = data.get('as_on_date')
        if isinstance(as_on_date, str):
            as_on_date = datetime.strptime(as_on_date, "%Y-%m-%d").date()
        as_on_date_str = as_on_date.strftime('%d/%m/%Y')
        partner = self.env['res.partner'].browse(partner_id) if partner_id else None
        partner_name = partner.name
        partner_credit = partner.property_payment_term_id.name if partner else None
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
            elif 180 <= days_diff <= 360:
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
                'greater_360': greater_360,
            })
        data_report = {
            'partner_credit': partner_credit,
            'partner_name': partner_name,
            'as_on_date': as_on_date,
            'as_on_date_str': as_on_date_str,
            'invoices': invoices_data,
            'total_balance': total_balance,
            'total_30': total_30,
            'total_30_60': total_30_60,
            'total_60_90': total_60_90,
            'total_90_180': total_90_180,
            'total_180_360': total_180_360,
            'total_greater_360': total_greater_360,
            'partner_zip': partner.zip,
            'partner_street': partner.street,
            'partner_street2': partner.street2,
            'partner_city': partner.city,
            'partner_state': partner.state_id.name,
            'partner_country': partner.country_id.name,
            'partner_phone': partner.phone,
        }
        return {
            'doc_ids': self.ids,
            'doc_model': 'soa.report',
            'data': data_report,
        }
