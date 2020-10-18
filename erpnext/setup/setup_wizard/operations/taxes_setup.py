# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, copy, os, json
from frappe.utils import flt
from erpnext.accounts.doctype.account.account import RootNotEditable

def create_sales_tax(args):
	country_wise_tax = get_country_wise_tax(args.get("country"))
	if country_wise_tax and len(country_wise_tax) > 0:
		for sales_tax, tax_data in country_wise_tax.items():
			make_tax_account_and_template(
				args.get("company_name"),
				tax_data, sales_tax)

def make_tax_account_and_template(company, tax_data, template_name=None):
	for tax in tax_data.get("taxes"):
		tax["tax_account"] = make_tax_account(company, tax.get("account_name"), tax.get("rate"), tax.get("account_number"))

	try:
		make_sales_and_purchase_tax_templates(company, tax_data, template_name)
	except frappe.NameError:
		if frappe.message_log: frappe.message_log.pop()
	except RootNotEditable:
		pass

def make_tax_account(company, account_name, tax_rate, account_number=None):
	tax_group = get_tax_account_group(company, account_number)

	if tax_group:
		try:
			return frappe.get_doc({
				"doctype":"Account",
				"company": company,
				"account_number": account_number,
				"parent_account": tax_group,
				"account_name": account_name,
				"is_group": 0,
				"report_type": "Balance Sheet",
				"root_type": "Liability",
				"account_type": "Tax",
				"tax_rate": flt(tax_rate) if tax_rate else None
			}).insert(ignore_permissions=True, ignore_mandatory=True)
		except frappe.NameError:
			if frappe.message_log: frappe.message_log.pop()
			abbr = frappe.get_cached_value('Company',  company,  'abbr')
			account = '{0} - {1}'.format(account_name, abbr) if not account_number else '{0} - {1} - {2}'.format(account_number, account_name, abbr)
			return frappe.get_doc('Account', account)

def make_sales_and_purchase_tax_templates(company, tax_data, template_name=None):
	if not template_name:
		template_name = tax_data.get("taxes", [])[0].get("account_name")

	sales_tax_template = {
		"doctype": "Sales Taxes and Charges Template",
		"title": template_name,
		"company": company,
		"is_default": tax_data.get("default", 0),
		'taxes': []
	}

	for tax_details in tax_data.get("taxes"):
		if tax_details.get("tax_account"):
			tax_details.update({
				"category": "Total",
				"charge_type": "On Net Total",
				"account_head": tax_details.get("tax_account", {}).get("name"),
				"description": tax_details.get("description") or tax_details.get("account_name")
			})
			sales_tax_template['taxes'].append(tax_details)

	# Sales
	if not tax_data.get("purchase_tax"):
		frappe.get_doc(copy.deepcopy(sales_tax_template)).insert(ignore_permissions=True)

	# Purchase
	if not tax_data.get("sales_tax"):
		purchase_tax_template = copy.deepcopy(sales_tax_template)
		purchase_tax_template["doctype"] = "Purchase Taxes and Charges Template"

		doc = frappe.get_doc(purchase_tax_template)
		doc.insert(ignore_permissions=True)

def get_tax_account_group(company, account_number=None):
	if account_number:
		tax_groups = frappe.get_all("Account",
			filters={"is_group": 1, "company": company, "account_number": ("in", (account_number[:-1], account_number[:-2]))},
			order_by="lft DESC")

		if tax_groups:
			tax_group = tax_groups[0]

	tax_group = frappe.db.get_value("Account",
		{"account_name": "Duties and Taxes", "is_group": 1, "company": company})
	if not tax_group:
		tax_group = frappe.db.get_value("Account", {"is_group": 1, "root_type": "Liability",
				"account_type": "Tax", "company": company})

	return tax_group

def get_country_wise_tax(country):
	data = {}
	with open (os.path.join(os.path.dirname(__file__), "..", "data", "country_wise_tax.json")) as countrywise_tax:
		data = json.load(countrywise_tax).get(country)

	return data
