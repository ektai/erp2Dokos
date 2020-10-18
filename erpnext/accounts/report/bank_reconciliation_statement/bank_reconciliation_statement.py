# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, nowdate
from frappe import _
from erpnext.accounts.doctype.bank_transaction.bank_transaction import get_bank_transaction_balance_on

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns()

	if not filters.get("bank_account"): return columns, []

	filters["account"] = frappe.db.get_value("Bank Account", filters.bank_account, "account")
	account_currency = frappe.db.get_value("Account", filters.account, "account_currency")

	data = get_entries(filters)

	from erpnext.accounts.utils import get_balance_on
	balance_as_per_system = get_balance_on(filters["account"], filters["report_date"])

	total_debit, total_credit = 0,0
	for d in data:
		total_debit += flt(d.debit)
		total_credit += flt(d.credit)

	amounts_not_reflected_in_system = get_amounts_not_reflected_in_system(filters)

	bank_bal = flt(balance_as_per_system) - flt(total_debit) + flt(total_credit) \
		+ amounts_not_reflected_in_system

	output = [
		{},
		get_balance_row(_("Bank Statement balance as per General Ledger"), balance_as_per_system, account_currency),
		{}
	]

	output += data
	output += [
		{
			"payment_entry": frappe.bold(_("Outstanding Cheques and Deposits to clear")),
			"debit": total_debit,
			"credit": total_credit,
			"account_currency": account_currency
		},
		{}
	]

	if amounts_not_reflected_in_system:
		output +=  get_entries_not_reflected(filters)

	output += [
		get_balance_row(_("Cheques and Deposits incorrectly cleared"), amounts_not_reflected_in_system,
			account_currency),
		{},
		get_balance_row(_("Calculated Bank Statement balance"), bank_bal, account_currency),
		{},
		get_bank_statement_row(filters, account_currency)
	]

	return columns, output

def get_columns():
	return [
		{
			"fieldname": "posting_date",
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"width": 90
		},
		{
			"fieldname": "payment_document",
			"label": _("Payment Document Type"),
			"fieldtype": "Data",
			"width": 220
		},
		{
			"fieldname": "payment_entry",
			"label": _("Payment Document"),
			"fieldtype": "Dynamic Link",
			"options": "payment_document",
			"width": 220
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "account_currency",
			"width": 120
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "account_currency",
			"width": 120
		},
		{
			"fieldname": "against_account",
			"label": _("Against Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 200
		},
		{
			"fieldname": "reference_no",
			"label": _("Reference"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "ref_date",
			"label": _("Ref Date"),
			"fieldtype": "Date",
			"width": 110
		},
		{
			"fieldname": "clearance_date",
			"label": _("Clearance Date"),
			"fieldtype": "Date",
			"width": 110
		},
		{
			"fieldname": "account_currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 100
		}
	]

def get_entries(filters):
	journal_entries = frappe.db.sql("""
		select "Journal Entry" as payment_document, jv.posting_date,
			jv.name as payment_entry, jvd.debit_in_account_currency as debit,
			jvd.credit_in_account_currency as credit, jvd.against_account,
			jv.cheque_no as reference_no, jv.cheque_date as ref_date, jv.clearance_date, jvd.account_currency
		from
			`tabJournal Entry Account` jvd, `tabJournal Entry` jv
		where jvd.parent = jv.name and jv.docstatus=1
			and jvd.account = %(account)s and jv.posting_date <= %(report_date)s
			and ifnull(jv.clearance_date, '4000-01-01') > %(report_date)s
			and ifnull(jv.is_opening, 'No') = 'No'""", filters, as_dict=1)

	payment_entries = frappe.db.sql("""
		select
			"Payment Entry" as payment_document, name as payment_entry,
			reference_no, reference_date as ref_date,
			if(paid_to=%(account)s, received_amount, 0) as debit,
			if(paid_from=%(account)s, paid_amount, 0) as credit,
			posting_date, ifnull(party,if(paid_from=%(account)s,paid_to,paid_from)) as against_account, clearance_date,
			if(paid_to=%(account)s, paid_to_account_currency, paid_from_account_currency) as account_currency
		from `tabPayment Entry`
		where
			(paid_from=%(account)s or paid_to=%(account)s) and docstatus=1
			and posting_date <= %(report_date)s
			and ifnull(clearance_date, '4000-01-01') > %(report_date)s
	""", filters, as_dict=1)

	pos_entries = frappe.db.sql("""
		select
			"Sales Invoice Payment" as payment_document, si.name as payment_entry,
			si.posting_date, si.customer as against_account, sip.clearance_date, si.remarks as reference_no,
			account.account_currency,
			if(si.is_return, 0, sip.amount) as debit,
			if(si.is_return, sip.amount, 0) as credit
		from `tabSales Invoice Payment` sip, `tabSales Invoice` si, `tabAccount` account
		where
			sip.account=%(account)s and si.docstatus=1 and sip.parent = si.name
			and account.name = sip.account and si.posting_date <= %(report_date)s and
			ifnull(sip.clearance_date, '4000-01-01') > %(report_date)s
		order by
			si.posting_date ASC, si.name DESC
	""", filters, as_dict=1)

	purchase_invoices = frappe.db.sql("""
		select
			"Purchase Invoice" as payment_document, pi.name as payment_entry,
			pi.remarks as reference_no, pi.due_date as ref_date,
			if(pi.is_return, ABS(pi.base_paid_amount), 0) as debit,
			if(pi.is_return, 0, ABS(pi.base_paid_amount)) as credit,
			pi.posting_date, pi.supplier as against_account, pi.clearance_date,
			account.account_currency
		from `tabPurchase Invoice` pi, `tabAccount` account
		where
			pi.docstatus=1 and pi.is_paid=1 and pi.cash_bank_account=%(account)s
			and account.name = pi.cash_bank_account
			and pi.posting_date <= %(report_date)s
			and ifnull(pi.clearance_date, '4000-01-01') > %(report_date)s
	""", filters, as_dict=1)

	return sorted(list(payment_entries)+list(journal_entries)+list(pos_entries)+list(purchase_invoices),
			key=lambda k: k['posting_date'] or getdate(nowdate()))

def get_amounts_not_reflected_in_system(filters):
	je_amount = frappe.db.sql("""
		select sum(jvd.debit_in_account_currency - jvd.credit_in_account_currency)
		from `tabJournal Entry Account` jvd, `tabJournal Entry` jv
		where jvd.parent = jv.name and jv.docstatus=1 and jvd.account=%(account)s
		and jv.posting_date > %(report_date)s and jv.clearance_date <= %(report_date)s
		and ifnull(jv.is_opening, 'No') = 'No' """, filters)

	je_amount = flt(je_amount[0][0]) if je_amount else 0.0

	pe_amount = frappe.db.sql("""
		select sum(if(paid_from=%(account)s, paid_amount * -1, received_amount))
		from `tabPayment Entry`
		where (paid_from=%(account)s or paid_to=%(account)s) and docstatus=1
		and posting_date > %(report_date)s and clearance_date <= %(report_date)s""", filters)

	pe_amount = flt(pe_amount[0][0]) if pe_amount else 0.0

	return je_amount + pe_amount

def get_entries_not_reflected(filters):
	je_entries = frappe.db.sql("""
		select "Journal Entry" as payment_document, jv.posting_date,
			jv.name as payment_entry, jvd.debit_in_account_currency as debit,
			jvd.credit_in_account_currency as credit, jvd.against_account,
			jv.cheque_no as reference_no, jv.cheque_date as ref_date, jv.clearance_date, jvd.account_currency
		from `tabJournal Entry Account` jvd, `tabJournal Entry` jv
		where jvd.parent = jv.name and jv.docstatus=1 and jvd.account=%(account)s
		and jv.posting_date > %(report_date)s and jv.clearance_date <= %(report_date)s
		and ifnull(jv.is_opening, 'No') = 'No' """, filters, as_dict=True)

	pe_entries = frappe.db.sql("""
		select
			"Payment Entry" as payment_document, name as payment_entry,
			reference_no, reference_date as ref_date,
			if(paid_to=%(account)s, received_amount, 0) as debit,
			if(paid_from=%(account)s, paid_amount, 0) as credit,
			posting_date, ifnull(party,if(paid_from=%(account)s,paid_to,paid_from)) as against_account, clearance_date,
			if(paid_to=%(account)s, paid_to_account_currency, paid_from_account_currency) as account_currency
		from `tabPayment Entry`
		where (paid_from=%(account)s or paid_to=%(account)s) and docstatus=1
		and posting_date > %(report_date)s and clearance_date <= %(report_date)s""", filters, as_dict=True)

	return sorted(list(je_entries)+list(pe_entries), key=lambda k: k['posting_date'] or getdate(nowdate()))

def get_balance_row(label, amount, account_currency):
	if flt(amount) > 0:
		return {
			"payment_entry": frappe.bold(label),
			"debit": amount,
			"credit": 0,
			"account_currency": account_currency
		}
	else:
		return {
			"payment_entry": frappe.bold(label),
			"debit": 0,
			"credit": abs(amount),
			"account_currency": account_currency
		}

def get_bank_statement_row(filters, account_currency):
	balance = get_bank_transaction_balance_on(filters["bank_account"], getdate(filters["report_date"]))

	return {
		"payment_entry": frappe.bold(_("Bank statement balance")),
		"debit": balance.get("balance") if balance.get("balance") > 0 else 0,
		"credit": balance.get("balance") if balance.get("balance") < 0 else 0,
		"account_currency": account_currency
	}