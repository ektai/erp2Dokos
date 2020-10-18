from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Sales"),
			"items": [
				{
					"type": "doctype",
					"name": "Customer",
					"description": _("Customer Database."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Quotation",
					"description": _("Quotes to Leads or Customers."),
					"onboard": 1,
					"dependencies": ["Item", "Customer"],
				},
				{
					"type": "doctype",
					"name": "Sales Order",
					"description": _("Confirmed orders from Customers."),
					"onboard": 1,
					"dependencies": ["Item", "Customer"],
				},
				{
					"type": "doctype",
					"name": "Sales Invoice",
					"description": _("Invoices for Customers."),
					"onboard": 1,
					"dependencies": ["Item", "Customer"],
				},
				{
					"type": "doctype",
					"name": "Subscription",
					"description": _("Manage Subscriptions."),
					"dependencies": ["Item", "Customer"],
				},
				{
					"type": "doctype",
					"name": "Blanket Order",
					"description": _("Blanket Orders from Customers."),
					"onboard": 1,
					"dependencies": ["Item", "Customer"],
				},
				{
					"type": "doctype",
					"name": "Sales Partner",
					"description": _("Manage Sales Partners."),
					"dependencies": ["Item"],
				},
				{
					"type": "doctype",
					"label": _("Sales Person"),
					"name": "Sales Person",
					"link": "Tree/Sales Person",
					"description": _("Manage Sales Person Tree."),
					"dependencies": ["Item", "Customer"],
				}
			]
		},
		{
			"label": _("Items and Pricing"),
			"items": [
				{
					"type": "doctype",
					"name": "Item",
					"description": _("All Products or Services."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Item Price",
					"description": _("Multiple Item prices."),
					"route": "#Report/Item Price",
					"dependencies": ["Item", "Price List"],
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Price List",
					"description": _("Price List master."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Item Group",
					"label": _("Item Group"),
					"link": "Tree/Item Group",
					"description": _("Tree of Item Groups."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Product Bundle",
					"description": _("Bundle items at time of sale."),
					"dependencies": ["Item"],
				},
				{
					"type": "doctype",
					"name": "Promotional Scheme",
					"description": _("Rules for applying different promotional schemes.")
				},
				{
					"type": "doctype",
					"name": "Pricing Rule",
					"description": _("Rules for applying pricing and discount."),
					"dependencies": ["Item"],
				},
				{
					"type": "doctype",
					"name": "Shipping Rule",
					"description": _("Rules for adding shipping costs."),
				},
				{
					"type": "doctype",
					"name": "Coupon Code",
					"description": _("Define coupon codes."),
				}

			]
		},
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Selling Settings",
					"description": _("Default settings for selling transactions."),
					"settings": 1,
				},
				{
					"type": "doctype",
					"name":"Terms and Conditions",
					"label": _("Terms and Conditions Template"),
					"description": _("Template of terms or contract."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Sales Taxes and Charges Template",
					"description": _("Tax template for selling transactions."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Lead Source",
					"description": _("Track Leads by Lead Source.")
				},
				{
					"type": "doctype",
					"label": _("Customer Group"),
					"name": "Customer Group",
					"link": "Tree/Customer Group",
					"description": _("Manage Customer Group Tree."),
				},
				{
					"type": "doctype",
					"name": "Contact",
					"description": _("All Contacts."),
				},
				{
					"type": "doctype",
					"name": "Address",
					"description": _("All Addresses."),
				},
				{
					"type": "doctype",
					"label": _("Territory"),
					"name": "Territory",
					"link": "Tree/Territory",
					"description": _("Manage Territory Tree."),
				},
				{
					"type": "doctype",
					"name": "Campaign",
					"description": _("Sales campaigns."),
				},
				{
					"type": "doctype",
					"name": "Brand",
					"description": _("Brand"),
				}
			]
		},
		{
			"label": _("Key Reports"),
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Sales Analytics",
					"doctype": "Sales Order",
					"onboard": 1,
				},
				{
					"type": "page",
					"name": "sales-funnel",
					"label": _("Sales Funnel"),
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Customer Acquisition and Loyalty",
					"doctype": "Customer",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Inactive Customers",
					"doctype": "Sales Order"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Ordered Items To Be Delivered",
					"doctype": "Sales Order"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Item-wise Sales History",
					"doctype": "Item"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Quotation Trends",
					"doctype": "Quotation"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Sales Order Trends",
					"doctype": "Sales Order"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Sales Person-wise Transaction Summary",
					"doctype": "Sales Order",
					"dependencies": ["Sales Person"]
				}
			]
		},
		{
			"label": _("Other Reports"),
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Lead Details",
					"doctype": "Lead"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Address And Contacts",
					"label": _("Customer Addresses And Contacts"),
					"doctype": "Address",
					"route_options": {
						"party_type": "Customer"
					}
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "BOM Search",
					"doctype": "BOM"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Available Stock for Packing Items",
					"doctype": "Item",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Pending SO Items For Purchase Request",
					"doctype": "Sales Order"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Customer Credit Balance",
					"doctype": "Customer"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Customers Without Any Sales Transactions",
					"doctype": "Customer"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Sales Partners Commission",
					"doctype": "Customer"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Territory Target Variance Based On Item Group",
					"doctype": "Territory",
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Sales Person Target Variance Based On Item Group",
					"doctype": "Sales Person",
					"dependencies": ["Sales Person"],
				},
			]
		},
		
	]
