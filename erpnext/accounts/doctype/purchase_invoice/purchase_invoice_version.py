# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

DOCTYPE_VERSION = "1.0.0"

def get_data():
	return [
		{
			"version": "1.0.0",
			"fields": ["naming_series", "supplier_name", "posting_date", "items", "credit_to", "accounting_journal"],
			"tables": {
				"items": ["item_name", "qty", "uom", "conversion_factor", "stock_qty", "rate",\
					"amount", "base_rate", "base_amount"]
			},
			"sanitize": False
		}
	]
