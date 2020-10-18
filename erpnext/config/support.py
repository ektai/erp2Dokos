from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Issues"),
			"items": [
				{
					"type": "doctype",
					"name": "Issue",
					"description": _("Support queries from customers."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Issue Type",
					"description": _("Issue Type."),
				},
				{
					"type": "doctype",
					"name": "Issue Priority",
					"description": _("Issue Priority."),
				}
			]
		},
		{
			"label": _("Warranty"),
			"items": [
				{
					"type": "doctype",
					"name": "Warranty Claim",
					"description": _("Warranty Claim against Serial No."),
				},
				{
					"type": "doctype",
					"name": "Serial No",
					"description": _("Single unit of an Item."),
				},
			]
		},
		{
			"label": _("Service Level Agreement"),
			"items": [
				{
					"type": "doctype",
					"name": "Service Level",
					"description": _("Service Level."),
				},
				{
					"type": "doctype",
					"name": "Service Level Agreement",
					"description": _("Service Level Agreement."),
				}
			]
		},
		{
			"label": _("Maintenance"),
			"items": [
				{
					"type": "doctype",
					"name": "Maintenance Schedule",
				},
				{
					"type": "doctype",
					"name": "Maintenance Visit",
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "page",
					"name": "support-analytics",
					"label": _("Support Analytics")
				},
				{
					"type": "report",
					"name": "Minutes to First Response for Issues",
					"doctype": "Issue",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Support Hours",
					"doctype": "Issue",
					"is_query_report": True
				},
			]
		},
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Support Settings",
					"label": _("Support Settings"),
				},
			]
		},
	]