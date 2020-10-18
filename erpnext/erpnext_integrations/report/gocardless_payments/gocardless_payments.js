// Copyright (c) 2020, Dokos SAS and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["GoCardless Payments"] = {
	filters: [
		{
			fieldtype: 'Link',
			label: __('Company'),
			fieldname: 'company',
			default: frappe.defaults.get_user_default("Company"),
			options: "Company",
			reqd: 1
		},
		{
			fieldtype: 'DateRange',
			label: __('Date Range'),
			fieldname: 'date_range',
			default: [frappe.datetime.add_months(frappe.datetime.get_today(),-3), frappe.datetime.get_today()],
			reqd: 1
		},
		{
			fieldtype: 'Link',
			label: __('Payment Gateway'),
			fieldname: 'payment_gateway',
			options: "Payment Gateway",
			get_query: function() {
				return {
					filters: {
						gateway_settings: "GoCardless Settings"
					}
				}
			}
		},
		{
			fieldtype: 'Link',
			label: __('Subscription'),
			fieldname: 'subscription',
			options: "Subscription"
		},
	]
};
