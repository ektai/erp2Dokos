# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

DOCTYPE_VERSION = "1.0.0"

def get_data():
	return [
		{
			"version": "1.0.0",
			"fields": ['posting_date', 'transaction_date', 'account', 'party_type', 'party',\
				'cost_center', 'debit', 'credit', 'account_currency', 'debit_in_account_currency',\
				'credit_in_account_currency', 'against', 'against_voucher_type', 'against_voucher',\
				'voucher_type', 'voucher_no', 'voucher_detail_no', 'project', 'remarks', 'is_opening',\
				'is_advance', 'fiscal_year', 'company', 'finance_book', 'due_date'],
			"tables": {},
			"sanitize": True
		}
	]
