from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Projects"),
			"items": [
				{
					"type": "doctype",
					"name": "Project",
					"description": _("Project master."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Task",
					"route": "#List/Task",
					"description": _("Project activity / task."),
					"onboard": 1,
				},
				{
					"type": "report",
					"route": "#List/Task/Gantt",
					"doctype": "Task",
					"name": "Gantt Chart",
					"description": _("Gantt chart of all tasks."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Project Template",
					"description": _("Make project from a template."),
				},
				{
					"type": "doctype",
					"name": "Project Type",
					"description": _("Define Project type."),
				},
				{
					"type": "doctype",
					"name": "Project Update",
					"description": _("Project Update."),
					"dependencies": ["Project"],
				},
			]
		},
		{
			"label": _("Time Tracking"),
			"items": [
				{
					"type": "doctype",
					"name": "Timesheet",
					"description": _("Timesheet for tasks."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Activity Type",
					"description": _("Types of activities for Time Logs"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Activity Cost",
					"description": _("Cost of various activities"),
					"dependencies": ["Activity Type"],
				},
			]
		},
		{
			"label": _("Reports"),
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Daily Timesheet Summary",
					"doctype": "Timesheet",
					"onboard": 1,
					"dependencies": ["Timesheet"],
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Project wise Stock Tracking",
					"doctype": "Project",
					"dependencies": ["Project"],
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Project Billing Summary",
					"doctype": "Project",
					"dependencies": ["Project"],
				},
			]
		},
		
	]
