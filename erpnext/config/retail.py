from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
            "label": _("Retail Operations"),
            "items": [
                 {
                    "type": "page",
                    "name": "point-of-sale",
                    "label": _("Point of Sale"),
                    "description": _("Point of Sale"),
					"onboard": 1,
					"dependencies": ["POS Profile"]
                },
                {
                    "type": "doctype",
                    "name": "POS Profile",
                    "label": _("Point-of-Sale Profile"),
                    "description": _("Setup default values for POS Invoices"),
					"onboard": 1,
                }
            ]
        },
        {
            "label": _("Loyalty Program"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Loyalty Program",
                    "label": _("Loyalty Program"),
                    "description": _("To make Customer based incentive schemes.")
                },
                {
                    "type": "doctype",
                    "name": "Loyalty Point Entry",
                    "label": _("Loyalty Point Entry"),
                    "description": _("To view logs of Loyalty Points assigned to a Customer.")
                }
            ]
        }
	]