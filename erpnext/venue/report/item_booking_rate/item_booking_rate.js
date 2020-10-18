// Copyright (c) 2020, Dokos SAS and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Booking Rate"] = {
	filters: [
		{
			fieldname: "period",
			label: __("Period"),
			fieldtype: "Select",
			options: [
				{ "value": "Monthly", "label": __("Monthly") },
				{ "value": "Quarterly", "label": __("Quarterly") },
				{ "value": "Half-Yearly", "label": __("Half-Yearly") },
				{ "value": "Yearly", "label": __("Yearly") }
			],
			default: "Monthly"
		},
		{
			fieldtype: 'DateRange',
			label: __('Date Range'),
			fieldname: 'date_range',
			default: [frappe.datetime.add_months(frappe.datetime.get_today(),-1), frappe.datetime.get_today()],
			reqd: 1
		},
		{
			fieldtype: 'Select',
			label: __('Status'),
			fieldname: 'status',
			default: "Confirmed",
			options: ["Confirmed", "Confirmed and not confirmed"],
			reqd: 1
		}
	]
};
