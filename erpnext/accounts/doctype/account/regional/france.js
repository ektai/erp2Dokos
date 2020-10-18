// Copyright (c) 2020, Dokos SAS and Contributors
// License: See license.txt

frappe.ui.form.on('Account', {
	onload: function(frm) {
		frm.set_query('balance_sheet_alternative_category', function(doc) {
			return {
				filters: {
					"is_group": 1,
					"company": doc.company,
					"root_type": doc.root_type == "Asset" ? "Liability" : "Asset"
				}
			};
		});
	},
})