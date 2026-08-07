# -*- coding: utf-8 -*-
{
    "name": "Sales Report - Delivery Date (Commitment Date)",
    "version": "17.0.1.0.0",
    "summary": "Adds Delivery Date (Commitment Date) to the Sales Analysis Pivot Report.",
    "description": """
Enhance your Odoo Sales Analysis with Delivery (Commitment) Date!

This module extends the **Sales Analysis** Pivot view by including the *Delivery Date* field (technically the `commitment_date` field from Sales Orders).  
It helps businesses gain better insights into their delivery commitments directly from the sales report.

Key Features:
=====================
✅ Adds Delivery Date (Commitment Date) to the Sales Analysis **Pivot View**  
✅ Enables analysis based on delivery timelines and commitments  
✅ Helps track on-time delivery performance  
✅ Simple, lightweight, and upgrade-safe  
✅ Works seamlessly with the Odoo Sales module  
✅ Compatible with both Odoo 17 Community & Enterprise editions  

Use Cases:
=====================
- Analyze sales based on delivery commitment periods  
- Identify delays or performance issues  
- Improve sales and delivery planning efficiency  

Technical Details:
=====================
- Field added: `commitment_date` (displayed as *Delivery Date*)  
- Affects: `sale.report` model and its **Pivot View only**  
- No changes to list or graph views  

""",
    "category": "Sales",
    "author": "Achaodoo",
    "maintainer": "Achaodoo",
    "website": "https://achaodoo.com/",
    "depends": ["sale"],
    "data": [
        "report/sale_report_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "license": "LGPL-3",
    "support": "hello.achaodoo@gmail.com",
    "installable": True,
    "application": False,
}