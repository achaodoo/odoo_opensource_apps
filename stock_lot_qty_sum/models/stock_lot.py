# -*- coding: utf-8 -*-
from odoo import api,  models
import itertools


class StockLot(models.Model):
    _inherit = 'stock.lot'

    @api.model
    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        """Override Odoo's `_read_group` to support SUM on non-stored computed fields.

        This method extends the standard Odoo grouping mechanism by enabling
        SUM aggregation on non-stored computed fields such as ``product_qty``.
        Normally, Odoo cannot aggregate these fields at the SQL level because
        they are not stored in the database. This override performs the SUM
        manually in Python and injects the results back into the grouped output.

        The logic:
        - Detect if special aggregations like ``product_qty:sum`` are requested.
        - Request ``id:recordset`` from the base `_read_group` to get the raw
          grouped records.
        - Iterate over each group and compute Python-level totals for the
          computed field.
        - Insert the computed aggregation values into the final grouped result.

        """
        SPECIAL = {'product_qty:sum'}
        if SPECIAL.isdisjoint(aggregates):
            return super()._read_group(domain, groupby, aggregates, having, offset, limit, order)

        base_aggregates = [*(agg for agg in aggregates if agg not in SPECIAL), 'id:recordset']
        base_result = super()._read_group(domain, groupby, base_aggregates, having, offset, limit, order)

        # base_result = [(a1, b1, records), (a2, b2, records), ...]
        result = []
        for *other, records in base_result:
            for index, spec in enumerate(itertools.chain(groupby, aggregates)):
                if spec in SPECIAL:
                    field_name = spec.split(':')[0]
                    other.insert(index, sum(records.mapped(field_name)))
            result.append(tuple(other))

        return result

    @api.model
    def read_group(self, domain, fields, *args, **kwargs):
        """Extend `read_group` to rewrite `product_qty` into `product_qty:sum`.

            When list views request grouping with ``product_qty`` included,
            Odoo normally expects a stored field for aggregation. This override
            transparently rewrites ``product_qty`` to ``product_qty:sum`` so that
            the custom `_read_group` logic can process it.

        """
        if 'product_qty' in fields:
            fields = ['product_qty:sum' if f == 'product_qty' else f for f in fields]
        return super().read_group(domain, fields, *args, **kwargs)
