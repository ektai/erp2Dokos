# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import re
import frappe
import erpnext
from frappe import _
from erpnext.accounts.page.bank_reconciliation.bank_reconciliation import BankReconciliation

@frappe.whitelist()
def auto_bank_reconciliation(bank_transactions):
	frappe.enqueue("erpnext.accounts.page.bank_reconciliation.auto_bank_reconciliation._reconcile_transactions", bank_transactions=bank_transactions)

def _reconcile_transactions(bank_transactions):
	bank_transactions = frappe.parse_json(bank_transactions) or []
	if not bank_transactions:
		frappe.throw(_("Please select a period with at least one transaction to reconcile"))

	for bank_transaction in bank_transactions:
		if not bank_transaction.get("amount"):
			continue

		if frappe.get_hooks('auto_reconciliation_methods'):
			for hook in frappe.get_hooks('auto_reconciliation_methods'):
				frappe.get_attr(hook)(bank_transaction)
		else:
			bank_reconciliation = AutoBankReconciliation(bank_transaction)
			bank_reconciliation.reconcile()

class AutoBankReconciliation:
	def __init__(self, bank_transaction):
		self.bank_transaction = bank_transaction
		self.reconciliation_by_id = {
			"prefixes": [],
			"matching_names": set()
		}
		self.documents = []

	def reconcile(self):
		# Reconcile by document name in references
		self.get_naming_series()
		self.check_transaction_references()
		if self.reconciliation_by_id.get("matching_names"):
			self.get_corresponding_documents()

		# Call regional reconciliation features
		regional_reconciliation(self)

		if self.documents:
			return
			BankReconciliation([self.bank_transaction], set(self.documents)).reconcile()

	def get_naming_series(self):
		self.reconciliation_by_id["prefixes"] = [x.get("name") for x in frappe.db.sql("""SELECT name FROM `tabSeries`""", as_dict=True) if x.get("name")]

	def check_transaction_references(self):
		for prefix in self.reconciliation_by_id.get("prefixes", []):
			for reference in [self.bank_transaction.get("reference_number"), self.bank_transaction.get("description")]:
				if reference:
					search_regex = r"{0}.*".format(prefix)
					match = re.findall(search_regex, reference)
					if match:
						for m in match:
							self.reconciliation_by_id["matching_names"].add(m)

	def get_corresponding_documents(self):
		for matching_name in self.reconciliation_by_id["matching_names"]:
			for doctype in ["Payment Entry", "Sales Invoice", "Purchase Invoice", "Expense Claim"]:
				if frappe.db.exists(doctype, matching_name):
					self.documents.append(frappe.get_doc(doctype, matching_name).as_dict())
					break

# Used for regional overrides
@erpnext.allow_regional
def regional_reconciliation(auto_bank_reconciliation):
	pass
