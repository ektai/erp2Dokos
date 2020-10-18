# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate, getdate

def execute(filters=None):
	if not filters: filters = {}

	filters["account"] = frappe.db.get_value("Bank Account", filters.bank_account, "account")

	columns = get_columns()
	data = get_entries(filters)

	return columns, data

def get_columns():
	return [
		_("Payment Document") + "::130",
		_("Payment Entry") + ":Dynamic Link/"+_("Payment Document")+":110",
		_("Posting Date") + ":Date:100",
		_("Cheque/Reference No") + "::120",
		_("Clearance Date") + ":Date:100",
		_("Against Account") + ":Link/Account:170",
		_("Amount") + ":Currency:120"
	]

def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"): conditions += " and posting_date>=%(from_date)s"
	if filters.get("to_date"): conditions += " and posting_date<=%(to_date)s"

	return conditions

def get_entries(filters):
	conditions = get_conditions(filters)
	journal_entries =  frappe.db.sql("""SELECT
			"Journal Entry", jv.name, jv.posting_date, jv.cheque_no,
			jv.clearance_date, jvd.against_account, jvd.debit - jvd.credit
		FROM 
			`tabJournal Entry Account` jvd, `tabJournal Entry` jv
		WHERE 
			jvd.parent = jv.name and jv.docstatus=1 and jvd.account = %(account)s {0}
			order by posting_date DESC, jv.name DESC""".format(conditions), filters, as_list=1)

	payment_entries =  frappe.db.sql("""SELECT
			"Payment Entry", name, posting_date, reference_no, clearance_date, party, 
			if(paid_from=%(account)s, paid_amount * -1, received_amount)
		FROM 
			`tabPayment Entry`
		WHERE
			docstatus=1 and (paid_from = %(account)s or paid_to = %(account)s) {0}
			order by posting_date DESC, name DESC""".format(conditions), filters, as_list=1)

	purchase_invoices =  frappe.db.sql("""SELECT
			"Purchase Invoice", name, posting_date, remarks, clearance_date, supplier,
			base_paid_amount * -1
		FROM
			`tabPurchase Invoice`
		WHERE
			docstatus=1 and is_paid=1 and cash_bank_account=%(account)s {0}
			order by posting_date DESC, name DESC""".format(conditions), filters, as_list=1)

	sales_invoices =  frappe.db.sql("""SELECT
			"Sales Invoice", si.name, si.posting_date, si.remarks, sip.clearance_date, si.customer,
			sip.base_amount
		FROM
			`tabSales Invoice Payment` sip
		LEFT JOIN
			`tabSales Invoice` si
		ON
			si.name = sip.parent
		WHERE
			si.docstatus=1 and si.is_pos=1 and sip.account=%(account)s {0}
			order by si.posting_date DESC, si.name DESC""".format(conditions), filters, as_list=1)

	mops = tuple([frappe.db.escape(x.parent) for x in frappe.get_all("Mode of Payment Account", {"default_account": filters.get("account")}, "parent")])
	if not mops:
		frappe.throw(_("Please create at least one mode of payment for this bank account first"))
	expense_claims =  frappe.db.sql("""SELECT
			"Expense Claim", name, posting_date, remark, clearance_date, employee,
			total_amount_reimbursed
		FROM
			`tabExpense Claim`
		WHERE
			docstatus=1 and mode_of_payment in ({1}) {0}
			order by posting_date DESC, name DESC""".format(conditions, ", ".join(mops)), filters, as_list=1)

	return sorted(journal_entries + payment_entries + purchase_invoices + sales_invoices, key=lambda k: k[2] or getdate(nowdate()))