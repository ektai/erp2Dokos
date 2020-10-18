from __future__ import unicode_literals
import frappe
from frappe import _

active_domains = frappe.get_active_domains()

def get_data():
	return [
		{
			"label": _("Accounting"),
			"items": [
				{
					"type": "doctype",
					"name": "Item",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Customer",
					"description": _("Customer database."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Supplier",
					"description": _("Supplier database."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Company",
					"description": _("Company (not Customer or Supplier) master."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Account",
					"label": _("Chart of Accounts"),
					"route": "#Tree/Account",
					"description": _("Tree of financial accounts."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Opening Invoice Creation Tool",
					"description": _("Create Opening Sales and Purchase Invoices"),
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Data Import and Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Data Import",
					"label": _("Import Data"),
					"icon": "octicon octicon-cloud-upload",
					"description": _("Import Data from CSV / Excel files."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Chart of Accounts Importer",
					"label": _("Chart of Accounts Importer"),
					"description": _("Import Chart of Accounts from CSV / Excel files"),
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Letter Head",
					"description": _("Letter Heads for print templates."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Email Account",
					"description": _("Add / Manage Email Accounts."),
					"onboard": 1,
				},

			]
		},
		{
			"label": _("Stock"),
			"items": [
				{
					"type": "doctype",
					"name": "Warehouse",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Brand",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "UOM",
					"label": _("Unit of Measure") + " (UOM)",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Stock Reconciliation",
					"onboard": 1,
				},
			]
		},
		{
			"label": _("CRM"),
			"items": [
				{
					"type": "doctype",
					"name": "Lead",
					"description": _("Database of potential customers."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"label": _("Customer Group"),
					"name": "Customer Group",
					"link": "Tree/Customer Group",
					"description": _("Manage Customer Group Tree."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"label": _("Territory"),
					"name": "Territory",
					"link": "Tree/Territory",
					"description": _("Manage Territory Tree."),
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Human Resources"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Employee Attendance Tool",
					"hide_count": True,
					"onboard": 1,
					"dependencies": ["Employee"]
				},
				{
					"type": "doctype",
					"name": "Salary Structure",
					"onboard": 1,
				},
			]
		}
	]