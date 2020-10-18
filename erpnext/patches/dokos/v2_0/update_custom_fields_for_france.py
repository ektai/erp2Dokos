import frappe
from erpnext.regional.france.setup import setup_company_independent_fixtures, default_accounts_mapping

def execute():
	frappe.reload_doc("setup", "doctype", "Company")
	companies = frappe.get_all("Company", fields=["name", "country"])

	if [x for x in companies if x.country == "France"]:
		setup_company_independent_fixtures()

	for company in companies:
		if company.country == "France":
			company_doc = frappe.get_doc("Company", company.name)
			accounts = frappe.get_all("Account", filters={"disabled": 0, "is_group": 0, "company": company.name}, fields=["name", "account_number"])
			account_map = default_accounts_mapping(accounts, company_doc)
			for account in account_map:
				if not company_doc.get(account):
					frappe.db.set_value("Company", company.name, account, account_map[account])
