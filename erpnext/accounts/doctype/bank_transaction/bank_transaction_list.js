// Copyright (c) 2019, Dokos SAS and Contributors
// License: See license.txt
frappe.provide("erpnext.accounts");

frappe.listview_settings['Bank Transaction'] = {
	add_fields: ["unallocated_amount"],
	get_indicator: function(doc) {
		if (doc.status === "Unreconciled") {
			return [__("Unreconciled", null, "Bank Transaction"), "orange", "status,=,Unreconciled"];
		} else if (doc.status === "Reconciled") {
			return [__("Reconciled", null, "Bank Transaction"), "green", "status,=,Reconciled"];
		} else if (doc.status === "Closed") {
			return [__("Closed"), "darkgray", "status,=,Closed"];
		} else if (doc.status === "Pending") {
			return [__("Closed"), "blue", "status,=,Pending"];
		} else if (doc.status === "Settled") {
			return [__("Closed"), "green", "status,=,Settled"];
		}
	},
	onload: function(list_view) {
		frappe.require('assets/js/bank-transaction-importer.min.js', function() {
			frappe.db.get_value("Plaid Settings", "Plaid Settings", "enabled", (r) => {
				if (r && r.enabled == "1") {
					list_view.page.add_menu_item(__("Synchronize this account"), function() {
						new erpnext.accounts.bankTransactionUpload('plaid');
					});
				}
			})
			list_view.page.add_menu_item(__("Upload an ofx statement"), function() {
				new erpnext.accounts.bankTransactionUpload('ofx');
			});
			list_view.page.add_menu_item(__("Upload a csv/xlsx statement"), function() {
				new erpnext.accounts.bankTransactionUpload('csv');
			});
		});
	},
	on_update: function(list_view) {
		list_view.refresh()
	}
};