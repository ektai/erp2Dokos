// Copyright (c) 2020, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Holiday List', {
	refresh: function(frm) {
		frm.add_custom_button(__("Add french bank holidays"), function() {
			const dialog = new frappe.ui.Dialog({
				title: __('Get French Bank Holidays'),
				fields: [
					{
						"label" : "Year",
						"fieldname": "year",
						"fieldtype": "Int",
						"reqd": 1,
						"default": frm.doc.from_date.substring(0, frm.doc.from_date.indexOf('-'))
					},
					{
						"label" : "zone",
						"fieldname": "zone",
						"fieldtype": "Select",
						"reqd": 1,
						"default": "Métropole",
						"options": [
							"Métropole",
							"Alsace-Moselle",
							"Guadeloupe",
							"Guyane",
							"Martinique",
							"Mayotte",
							"Nouvelle-Calédonie",
							"La Réunion",
							"Polynésie Française",
							"Saint-Barthélémy",
							"Saint-Martin",
							"Wallis-et-Futuna",
							"Saint-Pierre-et-Miquelon"
						]
					}
				],
				primary_action: function() {
					const data = dialog.get_values();
					frappe.xcall('erpnext.regional.france.hr.bank_holidays.get_french_bank_holidays', {year: data.year, zone: data.zone})
					.then(r => {
						Object.keys(r).forEach(function(element) {
							const holiday = frm.add_child("holidays");
							holiday.holiday_date = r[element];
							holiday.description = element;
						});
						frm.refresh_field("holidays");
					})
					dialog.hide();
				}
			});
			dialog.show();
		});
	}
});