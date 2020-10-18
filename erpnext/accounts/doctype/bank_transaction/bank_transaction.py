# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.controllers.status_updater import StatusUpdater
from frappe.utils import flt, getdate, fmt_money
from functools import reduce
from frappe import _
from itertools import zip_longest

class BankTransaction(StatusUpdater):
	def after_insert(self):
		self.unallocated_amount = flt(self.credit) - flt(self.debit)

	def before_insert(self):
		self.check_similar_entries()
		self.check_transaction_references()

	def before_save(self):
		self.check_bank_account_head()
		self.check_payment_types()
		self.calculate_totals()
		self.check_reconciliation_amounts()

	def on_submit(self):
		self.check_reconciliation_amounts()
		self.set_allocation_in_linked_docs()
		self.set_allocation_in_bank_transaction()
		self.set_payment_entries_clearance_date()
		self.set_status()

	def before_update_after_submit(self):
		self.check_bank_account_head()
		self.check_payment_types()
		self.calculate_totals()

	def on_update_after_submit(self):
		self.check_reconciliation_amounts()
		self.set_allocation_in_linked_docs()
		self.set_allocation_in_bank_transaction()
		self.set_payment_entries_clearance_date()
		self.set_status(update=True)

	def on_cancel(self):
		for entry in self.payment_entries:
			self.set_unreconciled_amount(entry, False)
		self.set_status(update=True)

	def check_similar_entries(self):
		filters = {"date": self.date, "credit": self.credit, "debit": self.debit, \
			"currency": self.currency, "bank_account": self.bank_account, "docstatus": 1}
		similar_entries = frappe.get_all("Bank Transaction", filters=filters)

		if similar_entries:
			if self.flags.import_statement:
				filters.update({"description": self.description})
				similar_entries = frappe.get_all("Bank Transaction", filters=filters)
				if similar_entries:
					raise frappe.DuplicateEntryError
			else:
				frappe.msgprint(_("The following entries exist already with the same date, debit, credit and currency:<br>{0}").format(", ".join([x.get("name") for x in similar_entries])))

	def check_transaction_references(self):
		if self.reference_number and frappe.db.exists("Bank Transaction", dict(bank_account=self.bank_account, reference_number=self.reference_number, docstatus=1)):
			frappe.throw(_("A bank transaction exists already with the same reference number for this bank account"), frappe.UniqueValidationError)

	def set_allocation_in_linked_docs(self):
		for i, j in zip_longest(self._doc_before_save.payment_entries, self.payment_entries):
			if not i:
				self.set_unreconciled_amount(j, True)
			elif not j:
				self.set_unreconciled_amount(i, False)
			elif i.name != j.name or i.get("allocated_amount") != j.get("allocated_amount"):
				self.set_unreconciled_amount(i, False)
				self.set_unreconciled_amount(j, True)

	def set_unreconciled_amount(self, payment, clear=True):
		unreconciled_amount = frappe.db.get_value(payment.payment_document, \
			payment.payment_entry, "unreconciled_amount")

		updated_amount = (flt(unreconciled_amount) - flt(payment.allocated_amount)) \
			if clear else (flt(unreconciled_amount) + flt(payment.allocated_amount))

		if payment.payment_document == "Payment Entry":
			paid_from, paid_to = frappe.db.get_value("Payment Entry", payment.payment_entry, ["paid_from", "paid_to"])

			if paid_from == self.bank_account_head:
				unreconciled_amount_field = "unreconciled_from_amount"
			elif paid_to == self.bank_account_head:
				unreconciled_amount_field = "unreconciled_to_amount"
			else:
				frappe.throw(_("This bank account could not be found on the selected payment document"))

			unreconciled_split_amount = frappe.db.get_value(payment.payment_document, payment.payment_entry, unreconciled_amount_field)
			updated_split_amount = (flt(unreconciled_split_amount) - flt(payment.allocated_amount)) if clear else (flt(unreconciled_split_amount) + flt(payment.allocated_amount))
			frappe.db.set_value(payment.payment_document, payment.payment_entry, unreconciled_amount_field, updated_split_amount)

		elif payment.payment_document == "Journal Entry":
			journal_entry_accounts = frappe.get_all("Journal Entry Account", \
				filters={"parent": payment.payment_entry, "parenttype": "Journal Entry", "account": self.bank_account_head}, \
				fields=["name", "unreconciled_amount"])
			total_split_amount = flt(payment.allocated_amount)
			for journal_entry_account in journal_entry_accounts:
				if total_split_amount > 0:
					unreconciled_split_amount = journal_entry_account.unreconciled_amount
					updated_split_amount = (flt(unreconciled_split_amount) - flt(payment.allocated_amount)) if clear else (flt(unreconciled_split_amount) + flt(payment.allocated_amount))
					frappe.db.set_value("Journal Entry Account", journal_entry_account.name, "unreconciled_amount", max(updated_split_amount, 0))
					total_split_amount = (total_split_amount - updated_split_amount) if updated_split_amount <= 0 else 0

		frappe.db.set_value(payment.payment_document, payment.payment_entry, "unreconciled_amount", updated_amount)

		if not clear:
			self.set_payment_entries_clearance_date(True)

		frappe.get_doc(payment.payment_document, payment.payment_entry).set_status(update=True)

	def set_allocation_in_bank_transaction(self):
		allocated_amount = sum([flt(x.get("allocated_amount", 0)) * (1 if x.get("payment_type") == "Debit" else -1) for x in self.payment_entries])\
			if self.payment_entries else 0
		
		transaction_amount = flt(self.credit) - flt(self.debit)

		self.db_set("allocated_amount", flt(allocated_amount) if allocated_amount else 0)
		self.db_set("unallocated_amount", (transaction_amount - flt(allocated_amount)) \
			if allocated_amount else transaction_amount)

		if transaction_amount == self.allocated_amount:
			self.db_set("status", "Reconciled")

		self.reload()

	def check_reconciliation_amounts(self):
		for payment_entry in self.payment_entries:
			unreconciled_amount = get_unreconciled_amount(payment_entry)

			if unreconciled_amount and payment_entry.allocated_amount and hasattr(payment_entry, "__unsaved"):
				if flt(payment_entry.allocated_amount) > flt(unreconciled_amount):
					frappe.throw(_("The allocated amount ({0}) is greater than the unreconciled amount ({1}) for {2} {3}.").format(\
						fmt_money(flt(payment_entry.allocated_amount), currency=self.currency), fmt_money(flt(unreconciled_amount), currency=self.currency), _(payment_entry.payment_document), payment_entry.payment_entry))

	def set_payment_entries_clearance_date(self, clear=False):
		for payment_entry in self.payment_entries:
			if payment_entry.payment_document in ["Payment Entry", "Journal Entry", "Purchase Invoice", "Expense Claim"]:
				self.set_header_clearance_date(payment_entry, clear)

			elif payment_entry.payment_document == "Sales Invoice":
				self.set_child_clearance_date(payment_entry, "Sales Invoice Payment", clear)

	def set_header_clearance_date(self, payment_entry, clear=False):
		frappe.db.set_value(payment_entry.payment_document, payment_entry.payment_entry, "clearance_date", None if clear else self.date)

	def set_child_clearance_date(self, payment_entry, child_table, clear=False):
		frappe.db.set_value(child_table, dict(parenttype=payment_entry.payment_document,
			parent=payment_entry.payment_entry), "clearance_date", None if clear else self.date)

	def check_payment_types(self):
		for payment in self.payment_entries:
			if payment.payment_document == "Sales Invoice":
				payment.payment_type = "Debit" if not frappe.db.get_value("Sales Invoice", payment.payment_entry, "is_return") else "Credit"
			elif payment.payment_document == "Purchase Invoice":
				payment.payment_type = "Credit" if not frappe.db.get_value("Purchase Invoice", payment.payment_entry, "is_return") else "Debit"
			if payment.payment_document == "Payment Entry":
				paid_from, paid_to = frappe.db.get_value("Payment Entry", payment.payment_entry, ("paid_from", "paid_to"))
				if self.bank_account_head == paid_from:
					payment.payment_type = "Credit"
				elif self.bank_account_head == paid_to:
					payment.payment_type = "Debit"
				else:
					frappe.throw(_("This bank account could not be found on the selected payment document"))
			if payment.payment_document == "Journal Entry":
				bank_account = frappe.db.get_value("Bank Account", self.bank_account, "account")
				debit_in_account_currency = frappe.db.get_value("Journal Entry Account", {"parent": payment.payment_entry, "account": bank_account}, "debit_in_account_currency")
				payment.payment_type = "Debit" if flt(debit_in_account_currency) > 0 else "Credit"
			if payment.payment_document == "Expense Claim":
				payment.payment_type = "Credit"

	def calculate_totals(self):
		self.total_debit = sum([x.allocated_amount for x in self.payment_entries if x.payment_type == "Debit"])
		self.total_credit = sum([x.allocated_amount for x in self.payment_entries if x.payment_type == "Credit"])

	@frappe.whitelist()
	def close_transaction(self):
		self.db_set("unallocated_amount", 0.0)
		self.db_set("status", "Closed")

	def check_bank_account_head(self):
		if not self.bank_account_head:
			self.bank_account_head = frappe.db.get_value("Bank Account", self.bank_account, "account")

def get_unreconciled_amount(payment_entry):
	return frappe.db.get_value(payment_entry.payment_document, payment_entry.payment_entry, "unreconciled_amount")

def get_bank_transaction_balance_on(bank_account, date):
	balance_query = frappe.get_all("Bank Transaction",
		filters={"date": ("<=", getdate(date)), "docstatus": 1, "bank_account": bank_account},
		fields=["SUM(credit)-SUM(debit) as balance", "currency"])

	balance = balance_query[0].get("balance") if balance_query[0].get("balance") else 0
	currency = balance_query[0].get("currency") if balance_query[0].get("currency") else None
	
	return {
		"balance": balance,
		"currency": currency,
		"formatted_balance": fmt_money(amount=balance, currency=currency)
	}

@frappe.whitelist()
def make_new_document(document_type, transactions=None):
	if document_type == "Payment Entry":
		return make_payment_entry(transactions)

def make_payment_entry(transactions=None):
	transactions = frappe.parse_json(transactions)
	payment_entry = frappe.new_doc("Payment Entry")

	if not transactions:
		return payment_entry
	else:
		amount = sum([x.get("amount") for x in transactions])
		bank_account = frappe.get_doc("Bank Account", transactions[0]["bank_account"])

		references = [x.get("reference_number") for x in transactions if x.get("reference_number")] or [x.get("description") for x in transactions if x.get("description")] or [x.get("name") for x in transactions]

		payment_entry.posting_date = transactions[0]["date"]
		payment_entry.company = bank_account.company
		payment_entry.bank_account = bank_account.name
		payment_entry.paid_amount = amount
		payment_entry.received_amount = amount
		payment_entry.reference_no = ",".join(references)
		payment_entry.reference_date = transactions[0]["date"]

		if amount > 0:
			payment_entry.payment_type = "Receive"
			payment_entry.party_type = "Customer"
			payment_entry.paid_to = bank_account.account
			payment_entry.paid_to_account_currency = transactions[0]["currency"]
		else:
			payment_entry.payment_type = "Pay"
			payment_entry.party_type = "Supplier"
			payment_entry.paid_from = bank_account.account
			payment_entry.paid_from_account_currency = transactions[0]["currency"]

		return payment_entry