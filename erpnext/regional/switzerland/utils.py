# Copyright (c) 2019, Dokos SAS and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from erpnext.accounts.page.bank_reconciliation.auto_bank_reconciliation import AutoBankReconciliation

def regional_reconciliation(auto_bank_reconciliation):
	for dt in ["Sales Invoice", "Purchase Invoice"]:
		if frappe.db.exists("Custom Field", {"fieldname": "esr_reference", "dt": dt}):
			auto_bank_reconciliation.documents.extend(match_esr_reference(dt, auto_bank_reconciliation))

def match_esr_reference(doctype, auto_bank_reconciliation):
	esr_reference_docs = []
	for reference in [auto_bank_reconciliation.bank_transaction.get("reference_number"), auto_bank_reconciliation.bank_transaction.get("description")]:
		if reference:
			esr_reference_doc = frappe.db.get_value(doctype, dict(esr_reference=reference.replace(" ", "")))
			if esr_reference_doc:
				esr_reference_docs.append(frappe.get_doc(doctype, esr_reference_doc).as_dict())
		
	return esr_reference_docs