// Copyright (c) 2020, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subscription Template', {
	refresh(frm) {
		frm.page.clear_actions_menu();
		if (!frm.is_new()) {
			frm.page.add_action_item(__('Make a subscription'), function() {
				frm.trigger('make_new_subscription');
			});
		}
	},

	make_new_subscription(frm) {
		const dialog = new frappe.ui.Dialog({
			title: __('Create a new subscription'),
			fields: [
				{
					"label" : "Company",
					"fieldname": "company",
					"fieldtype": "Link",
					"reqd": 1,
					"default": frappe.defaults.get_user_default("Company"),
					"options": "Company"
				},
				{
					"label" : "Customer",
					"fieldname": "customer",
					"fieldtype": "Link",
					"reqd": 1,
					"options": "Customer"
				},
				{
					"label" : "Start Date",
					"fieldname": "start_date",
					"fieldtype": "Date",
					"reqd": 1,
					"default": frappe.datetime.get_today()
				}
			],
			primary_action: function() {
				const values = dialog.get_values();
				const args = Object.assign(values, {"template": frm.doc.name})

				frappe.call({
					method: "erpnext.accounts.doctype.subscription_template.subscription_template.make_subscription",
					args: args,
				}).then(r => {
					if (r && !r.exc) {
						frappe.show_alert({message:__("The subscription has been created"), indicator:'green'});
						frm.reload_doc();
					} else {
						frappe.show_alert({message:__("An error prevented the subscription's creation"), indicator:'red'});
					}
				})
				dialog.hide()
			}
		})
		dialog.show()
	}
});
