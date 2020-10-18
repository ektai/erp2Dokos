# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

DOCTYPE_VERSION = "1.0.0"

def get_data():
	return [
		{
			"version": "1.0.0",
			"fields": ["naming_series", "customer_name", "company", "posting_date", "currency", "conversion_rate", \
				"selling_price_list", "price_list_currency", "plc_conversion_rate", "items", "base_net_total", \
				"base_grand_total", "grand_total", "debit_to", "taxes", "advances"],
			"tables": {
				"items": ['item_name', 'description', 'uom', 'conversion_factor', 'rate', 'amount', \
					'base_rate', 'base_amount', 'income_account', 'cost_center'],
				"taxes": ["charge_type", "account_head", "description"],
				"advances": ["reference_type", "reference_name", "advance_amount", "allocated_amount"]
			},
			"sanitize": False
		}
	]
