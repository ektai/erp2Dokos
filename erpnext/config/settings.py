from __future__ import unicode_literals
from frappe import _
from frappe.desk.moduleview import add_setup_section

def get_data():
	data = [
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Global Defaults",
					"label": _("dokos Settings"),
					"description": _("Set Default Values like Company, Currency, Current Fiscal Year, etc."),
					"hide_count": True,
					"settings": 1,
				}
			]
		},
		{
			"label": _("Printing"),
			"items": [
				{
					"type": "doctype",
					"name": "Letter Head",
					"description": _("Letter Heads for print templates."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Print Heading",
					"description": _("Titles for print templates e.g. Proforma Invoice.")
				},
				{
					"type": "doctype",
					"name": "Address Template",
					"description": _("Country wise default Address Templates")
				},
				{
					"type": "doctype",
					"name": "Terms and Conditions",
					"description": _("Standard contract terms for Sales or Purchase.")
				},
			]
		},
		{
			"label": _("Customize"),
			"items": [
				{
					"type": "doctype",
					"name": "Authorization Rule",
					"description": _("Create rules to restrict transactions based on values.")
				}
			]
		},
		{
			"label": _("Email"),
			"items": [
				{
					"type": "doctype",
					"name": "Email Digest",
					"description": _("Create and manage daily, weekly and monthly email digests.")
				},
				{
					"type": "doctype",
					"name": "SMS Settings",
					"description": _("Setup SMS gateway settings")
				},
			]
		}
	]

	for module, label, icon in (
		("accounts", _("Accounting"), "fas fa-book"),
		("stock", _("Stock"), "fas fa-warehouse"),
		("selling", _("Selling"), "fas fa-cash-register"),
		("buying", _("Buying"), "fas fa-shopping-bag"),
		("hr", _("Human Resources"), "fas fa-users"),
		("support", _("Support"), "fas fa-headset")):

		add_setup_section(data, "erpnext", module, label, icon)

	return data
