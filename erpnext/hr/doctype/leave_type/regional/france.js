// Copyright (c) 2020, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Type', {
	refresh: function(frm) {
		// For translations
		// __("Custom Formula")
		frm.set_df_property("earned_leave_frequency", "options", ["Monthly", "Quarterly", "Half-Yearly", "Yearly", "Custom Formula"]);
		frm.set_df_property("earned_leave_frequency_formula", "options", ["Congés payés sur jours ouvrables", "Congés payés sur jours ouvrés"]);
	}
});