from odoo import models, fields
from odoo.exceptions import ValidationError
import datetime
from datetime import datetime

class Chequetracker(models.TransientModel):
    """Generate a cheque tracker report for a selected date range.
    This wizard filters cheque payments by payment type and date range,
    retrieves the associated cheque tracker status, and prepares the data
    for the QWeb PDF report.
    """

    _name = "tracker.report"
    _description = "Cheque Tracker report"

    date_start = fields.Date('Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date('Date End', required=True, default=fields.Date.context_today)
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
    ], string='Payment Type', default='inbound', required=True)


    def _get_data(self):
        """Retrieve and prepare data for the cheque tracker report.
        Retrieves cheque payments matching the selected payment type and
        date range, along with their transaction reference, partner,
        cheque amount, and tracker status.
        """
        lines = []
        sl = 0
        date_start = self.date_start
        date_end = self.date_end
        payment_type = self.payment_type

        if payment_type:

            query = """

                    select m.name as ref,m.date as date,r.name as partner_name,p.amount as cheque_amount,c.name as cheque_name
                    from account_payment as p 
                    left join account_move as m on p.move_id=m.id 
                    left join res_partner as r on p.partner_id=r.id
                    left join cheque_tracker_status as c on c.id=p.cheque_tracker_status_id
                    where p.payment_type=%s and m.date between %s and %s and p.cheque_tracker_status_id is not null

                    """

            self.env.cr.execute(query, (
                payment_type,date_start, date_end
            ))
            for row in self.env.cr.dictfetchall():
                sl += 1
                ref = row['ref'] if row['ref'] else " "
                date = row['date'] if row['date'] else " "
                date = datetime.strptime(str(date), '%Y-%m-%d').date().strftime('%d-%m-%Y')
                partner_name = row['partner_name'] if row['partner_name'] else ""
                cheque_amount = row['cheque_amount'] if row['cheque_amount'] else 0.0
                cheque_name = row['cheque_name'] if row['cheque_name'] else 0.0


                date_start = self.date_start
                date_end = self.date_end


                res = {
                    'sl_no': sl,
                    'ref': ref,
                    'date': date,
                    'partner_name': partner_name if partner_name else " ",
                    'cheque_amount': cheque_amount if cheque_amount else 0.0,
                    'cheque_name': cheque_name if cheque_name else "",


                }

                lines.append(res)

        if self.date_start:
            date_start_doc = datetime.strptime(str(date_start), '%Y-%m-%d').date().strftime('%d-%m-%Y')
        if self.date_end:
            date_end_doc = datetime.strptime(str(date_end), '%Y-%m-%d').date().strftime('%d-%m-%Y')

        if not lines:
            raise ValidationError("No data available for printing.")
        datas = {
            'ids': self,
            'model': 'tracker.report',
            'form': lines,
            'start_date': self.date_start,
            'end_date': self.date_end,
            'date_start_doc':date_start_doc,
            'date_end_doc':date_end_doc

        }

        return datas

    def action_get_report(self):
        """Generate the cheque tracker PDF report.
        Retrieves the filtered cheque tracker data and triggers the
        configured QWeb PDF report action.
        """
        datas = self._get_data()
        return self.env.ref('cheque_tracker_alerts.action_tracker_report').report_action([], data=datas)

