from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Payments"),
			"items": [
				{
					"type": "doctype",
					"name": "Stripe Settings",
					"description": _("Stripe payment gateway settings"),
				},
				{
					"type": "doctype",
					"name": "GoCardless Settings",
					"description": _("GoCardless payment gateway settings"),
				},
				{
					"type": "doctype",
					"name": "Sepa Mandate",
					"description": _("GoCardless SEPA Mandate"),
				}
			]
		},
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Woocommerce Settings"
				},
				{
					"type": "doctype",
					"name": "Shopify Settings",
					"description": _("Connect Shopify with dokos"),
				},
				{
					"type": "doctype",
					"name": "Amazon MWS Settings",
					"description": _("Connect Amazon with dokos"),
				},
				{
					"type": "doctype",
					"name": "Plaid Settings",
					"description": _("Connect your bank accounts to dokos"),
				},
				{
					"type": "doctype",
					"name": "Exotel Settings",
					"description": _("Connect your Exotel Account to ERPNext and track call logs"),
				}
			]
		}
	]
