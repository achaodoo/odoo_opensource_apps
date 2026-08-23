# -*- coding: utf-8 -*-
import json
from odoo import http
import werkzeug
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from odoo.http import content_disposition, request, serialize_exception as _serialize_exception
import functools
import base64


def serialize_exception(f):
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return werkzeug.exceptions.InternalServerError(json.dumps(error))
    return wrap


class ReceiptRegisterReport(http.Controller):

    ############ Download Receipt Register Report ########################
    @http.route('/web/binary/export_receipt_register_report', type='http', auth="user", sitemap=False)
    @serialize_exception
    def download_receipt_register_report(self, id, model, **kw):
        Model = request.env[model]
        case = Model.browse(int(id))
        filename = 'Receipt Register.xlsx'
        if case and case.report_file:
            file_data = base64.b64decode(case.report_file)
            return request.make_response(file_data,
                                         headers=[
                                             ('Content-Disposition', content_disposition(filename)),
                                             ('Content-Type', 'application/vnd.ms-excel'),
                                             ('Content-Length', len(filename))],
                                         )
