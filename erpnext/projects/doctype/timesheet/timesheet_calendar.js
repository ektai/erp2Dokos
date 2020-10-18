frappe.views.calendar["Timesheet"] = {
	field_map: {
		"start": "start_date",
		"end": "end_date",
		"name": "parent",
		"id": "name",
		"allDay": "allDay",
		"child_name": "name",
		"title": "title"
	},
	gantt: true,
	filters: [
		{
			"fieldtype": "Link",
			"fieldname": "project",
			"options": "Project",
			"label": __("Project")
		},
		{
			"fieldtype": "Link",
			"fieldname": "employee",
			"options": "Employee",
			"label": __("Employee")
		}
	],
	get_events_method: "erpnext.projects.doctype.timesheet.timesheet.get_events"
}
