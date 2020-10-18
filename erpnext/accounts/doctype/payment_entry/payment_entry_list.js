// Copyright (c) 2019, Dokos SAS and Contributors
// License: See license.txt

frappe.listview_settings['Payment Entry'] = {
	get_indicator: function(doc) {
		if (doc.docstatus == 1) {
			return [__(doc.status, null, "Payment Entry"), doc.status === "Reconciled" ? "green": "orange", `status,==,${doc.status}`];
		}
	},
	onload: function(listview) {
		if (listview.page.fields_dict.party_type) {
			listview.page.fields_dict.party_type.get_query = function() {
				return {
					"filters": {
						"name": ["in", Object.keys(frappe.boot.party_account_types)],
					}
				};
			};
		}
	}
};