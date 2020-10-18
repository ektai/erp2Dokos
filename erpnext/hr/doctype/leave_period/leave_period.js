// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Period', {
	refresh: (frm)=>{
		frm.set_df_property("grant_leaves", "hidden", frm.doc.__islocal ? 1:0);
		if(!frm.is_new()) {
			frm.add_custom_button(__('Grant Leaves'), function () {
				frm.trigger("grant_leaves");
			});
		}
		frm.trigger("enable_disable_optional_holidays")
	},
	from_date: (frm)=>{
		if (frm.doc.from_date && !frm.doc.to_date) {
			var a_year_from_start = frappe.datetime.add_months(frm.doc.from_date, 12);
			frm.set_value("to_date", frappe.datetime.add_days(a_year_from_start, -1));
		}
	},
	onload: (frm) => {
		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			}
		})
	},
	grant_leaves: function(frm) {
		var d = new frappe.ui.Dialog({
			title: __('Grant Leaves'),
			fields: [
				{
					"label": __("Filter Employees By (Optional)"),
					"fieldname": "sec_break",
					"fieldtype": "Section Break",
				},
				{
					"label": __("Employee Grade"),
					"fieldname": "grade",
					"fieldtype": "Link",
					"options": "Employee Grade"
				},
				{
					"label": __("Department"),
					"fieldname": "department",
					"fieldtype": "Link",
					"options": "Department"
				},
				{
					"fieldname": "col_break",
					"fieldtype": "Column Break",
				},
				{
					"label": __("Designation"),
					"fieldname": "designation",
					"fieldtype": "Link",
					"options": "Designation"
				},
				{
					"label": __("Employee"),
					"fieldname": "employee",
					"fieldtype": "Link",
					"options": "Employee"
				},
				{
					"fieldname": "sec_break",
					"fieldtype": "Section Break",
				},
				{
					"label": __("Add unused leaves from previous allocations"),
					"fieldname": "carry_forward",
					"fieldtype": "Check"
				}
			],
			primary_action: function() {
				var data = d.get_values();

				frappe.call({
					doc: frm.doc,
					method: "grant_leave_allocation",
					args: data,
					callback: function(r) {
						if(!r.exc) {
							d.hide();
							frm.reload_doc();
						}
					}
				});
			},
			primary_action_label: __('Grant', null, 'Leave Period')
		});
		d.show();
	},
	leave_types(frm) {
		frm.trigger("enable_disable_optional_holidays")
	},
	enable_disable_optional_holidays(frm) {
		const leave_types = frm.doc.leave_types.map(f => {return f.leave_type})
		frappe.db.get_list("Leave Type", {
			filters: { 'name': ["in", leave_types]},
			fields: ["is_optional_leave"]
		}).then((data) => {
			const result = data.filter(f => f.is_optional_leave == 1)
			frm.toggle_display('optional_holiday_list', result.length)
		})
	}
});


frappe.tour['Leave Period'] = [
	{
		fieldname: "from_date",
		title: __("From Date"),
		description: __("Initial date for the period.")
	},
	{
		fieldname: "to_date",
		title: __("To Date"),
		description: __("Final date for the period.")
	},
	{
		fieldname: "is_active",
		title: __("Is Active"),
		description: __("This period is active/inactive.")
	},
	{
		fieldname: "company",
		title: __("Company"),
		description: __("Company this period is linked with.")
	},
	{
		fieldname: "optional_holiday_list",
		title: __("Holiday List for Optional Leave"),
		description: __("Holiday list to use specifically with optional leaves.")
	}
]