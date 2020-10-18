import frappe
from collections import defaultdict

def execute():
	frappe.reload_doc("accounts", "doctype", "payment_entry")
	for payment in frappe.get_all("Payment Entry", filters={"status": "Unreconciled"}, fields=["name", "paid_amount", "payment_type"]):
		frappe.db.set_value("Payment Entry", payment.name, "unreconciled_from_amount", payment.paid_amount if payment.payment_type in ("Pay", "Internal Transfer") else 0.0, update_modified=False)
		frappe.db.set_value("Payment Entry", payment.name, "unreconciled_to_amount", payment.paid_amount if payment.payment_type in ("Receive", "Internal Transfer") else 0.0, update_modified=False)

	frappe.reload_doc("accounts", "doctype", "bank_transaction")
	bank_transactions = frappe.get_all("Bank Transaction", fields=["name", "bank_account"])
	bank_accounts = [x.bank_account for x in bank_transactions]

	accounts = defaultdict(dict)
	for account in bank_accounts:
		accounts[account] = frappe.db.get_value("Bank Account", account, "account")


	for bank_transaction in bank_transactions:
		frappe.db.set_value("Bank Transaction", bank_transaction.name, "bank_account_head", accounts.get(bank_transaction.bank_account), update_modified=False)
