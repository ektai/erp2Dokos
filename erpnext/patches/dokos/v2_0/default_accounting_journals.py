import frappe
from erpnext.setup.setup_wizard.operations.company_setup import create_accounting_journals

def execute():
	frappe.reload_doc("accounts", "doctype", "Accounting Journal")
	frappe.local.lang = frappe.db.get_default("lang") or 'en'
	for company in frappe.get_all("Company", fields=["name", "default_bank_account"]):
		create_accounting_journals(company.default_bank_account, company.name)