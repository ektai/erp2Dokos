# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, get_datetime, flt
from collections import defaultdict
from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data
from erpnext.accounts.doctype.pos_invoice_merge_log.pos_invoice_merge_log import merge_pos_invoices

class POSClosingEntry(Document):
	def validate(self):
		user = frappe.get_all('POS Closing Entry',
			filters = { 'user': self.user, 'docstatus': 1 },
			or_filters = {
					'period_start_date': ('between', [self.period_start_date, self.period_end_date]),
					'period_end_date': ('between', [self.period_start_date, self.period_end_date])
			})

		if user:
			frappe.throw(_("POS Closing Entry {} against {} between selected period"
				.format(frappe.bold("already exists"), frappe.bold(self.user))), title=_("Invalid Period"))

		if frappe.db.get_value("POS Opening Entry", self.pos_opening_entry, "status") != "Open":
			frappe.throw(_("Selected POS Opening Entry should be open."), title=_("Invalid Opening Entry"))

	def on_submit(self):
		merge_pos_invoices(self.pos_transactions)
		opening_entry = frappe.get_doc("POS Opening Entry", self.pos_opening_entry)
		opening_entry.pos_closing_entry = self.name
		opening_entry.set_status()
		opening_entry.save()

	def get_payment_reconciliation_details(self):
		currency = frappe.get_cached_value('Company', self.company,  "default_currency")
		return frappe.render_template("erpnext/accounts/doctype/pos_closing_entry/closing_voucher_details.html",
			{"data": self, "currency": currency})

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
	cashiers_list = frappe.get_all("POS Profile User", filters=filters, fields=['user'])
	return [c['user'] for c in cashiers_list]

@frappe.whitelist()
def get_pos_invoices(start, end, user):
	data = frappe.db.sql("""
	select
		name, timestamp(posting_date, posting_time) as "timestamp"
	from
		`tabPOS Invoice`
	where
		owner = %s and docstatus = 1 and
		(consolidated_invoice is NULL or consolidated_invoice = '')
	""", (user), as_dict=1)

	data = list(filter(lambda d: get_datetime(start) <= get_datetime(d.timestamp) <= get_datetime(end), data))
	# need to get taxes and payments so can't avoid get_doc
	data = [frappe.get_doc("POS Invoice", d.name).as_dict() for d in data]

	return data

def make_closing_entry_from_opening(opening_entry):
	closing_entry = frappe.new_doc("POS Closing Entry")
	closing_entry.pos_opening_entry = opening_entry.name
	closing_entry.period_start_date = opening_entry.period_start_date
	closing_entry.period_end_date = frappe.utils.get_datetime()
	closing_entry.pos_profile = opening_entry.pos_profile
	closing_entry.user = opening_entry.user
	closing_entry.company = opening_entry.company
	closing_entry.grand_total = 0
	closing_entry.net_total = 0
	closing_entry.total_quantity = 0

	invoices = get_pos_invoices(closing_entry.period_start_date, closing_entry.period_end_date, closing_entry.user)

	pos_transactions = []
	taxes = []
	payments = []
	for detail in opening_entry.balance_details:
		payments.append(frappe._dict({
			'mode_of_payment': detail.mode_of_payment,
			'opening_amount': detail.opening_amount,
			'expected_amount': detail.opening_amount
		}))

	for d in invoices:
		pos_transactions.append(frappe._dict({
			'pos_invoice': d.name,
			'posting_date': d.posting_date,
			'grand_total': d.grand_total,
			'customer': d.customer
		}))
		closing_entry.grand_total += flt(d.grand_total)
		closing_entry.net_total += flt(d.net_total)
		closing_entry.total_quantity += flt(d.total_qty)

		for t in d.taxes:
			existing_tax = [tx for tx in taxes if tx.account_head == t.account_head and tx.rate == t.rate]
			if existing_tax:
				existing_tax[0].amount += flt(t.tax_amount);
			else:
				taxes.append(frappe._dict({
					'account_head': t.account_head,
					'rate': t.rate,
					'amount': t.tax_amount
				}))

		for p in d.payments:
			existing_pay = [pay for pay in payments if pay.mode_of_payment == p.mode_of_payment]
			if existing_pay:
				existing_pay[0].expected_amount += flt(p.amount);
			else:
				payments.append(frappe._dict({
					'mode_of_payment': p.mode_of_payment,
					'opening_amount': 0,
					'expected_amount': p.amount
				}))

	closing_entry.set("pos_transactions", pos_transactions)
	closing_entry.set("payment_reconciliation", payments)
	closing_entry.set("taxes", taxes)

	return closing_entry
