import frappe
from frappe.utils import flt

def execute():
	frappe.reload_doc("accounts", "doctype", "bank_transaction")
	frappe.reload_doc("accounts", "doctype", "bank_transaction_payments")
	frappe.reload_doc("accounts", "doctype", "payment_entry")
	frappe.reload_doc("accounts", "doctype", "sales_invoice")
	frappe.reload_doc("accounts", "doctype", "purchase_invoice")
	frappe.reload_doc("hr", "doctype", "expense_claim")
	frappe.reload_doc("accounts", "doctype", "journal_entry")

	try:
		for transaction in frappe.get_all("Bank Transaction", filters={"transaction_id": ("!=", "")}, fields=["name", "transaction_id", "reference_number"]):
			if not transaction.reference_number:
				frappe.db.set_value("Bank Transaction", transaction.name, "reference_number", "transaction_id")
	except Exception:
		pass

	for payment_entry in frappe.get_all("Payment Entry", \
		filters={"docstatus": 1, "clearance_date": ["is", "not set"]}, fields=["paid_amount", "received_amount", "payment_type", "name"]):
		frappe.db.set_value("Payment Entry", payment_entry.name, "unreconciled_amount", \
			flt(payment_entry.paid_amount) if payment_entry.payment_type == "Pay" else flt(payment_entry.received_amount))

	for sales_invoice_payment in frappe.get_all("Sales Invoice Payment", \
		filters={"mode_of_payment": ["is", "set"], "clearance_date": ["is", "not set"]}, fields=["sum(base_amount) as amount", "parent"], group_by="parent"):
		is_return = frappe.db.get_value("Sales Invoice", sales_invoice_payment.parent, "is_return")
		frappe.db.set_value("Sales Invoice", sales_invoice_payment.parent, "unreconciled_amount", \
			(flt(sales_invoice_payment.amount) * -1) if is_return else flt(sales_invoice_payment.amount))

	for purchase_invoice in frappe.get_all("Purchase Invoice", \
		filters={"docstatus": 1, "clearance_date": ["is", "not set"], "mode_of_payment": ["is", "set"]}, fields=["base_paid_amount", "name", "is_return"]):
		frappe.db.set_value("Purchase Invoice", purchase_invoice.name, "unreconciled_amount", \
			(flt(purchase_invoice.base_paid_amount) * -1) if purchase_invoice.is_return else flt(purchase_invoice.base_paid_amount))

	for expense_claim in frappe.get_all("Expense Claim", \
		filters={"docstatus": 1, "clearance_date": ["is", "not set"], "mode_of_payment": ["is", "set"]}, fields=["total_claimed_amount", "name"]):
		frappe.db.set_value("Expense Claim", expense_claim.name, "unreconciled_amount", \
			flt(expense_claim.total_claimed_amount))

	for journal_entry in frappe.get_all("Journal Entry", \
		filters={"docstatus": 1, "clearance_date": ["is", "not set"]}):
		doc = frappe.get_doc("Journal Entry", journal_entry.name)
		doc.update_unreconciled_amount()

	for transaction in frappe.get_all("Bank Transaction"):
		doc = frappe.get_doc("Bank Transaction", transaction.name)
		debit = sum([x.allocated_amount for x in doc.payment_entries if x.payment_type == "Debit"])
		credit = sum([x.allocated_amount for x in doc.payment_entries if x.payment_type == "Credit"])

		frappe.db.set_value("Bank Transaction", doc.name, "total_debit", debit)
		frappe.db.set_value("Bank Transaction", doc.name, "total_credit", credit)
