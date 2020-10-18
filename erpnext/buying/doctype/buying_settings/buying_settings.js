// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Buying Settings', {
	// refresh: function(frm) {

	// }
});

frappe.tour['Buying Settings'] = [
	{
		fieldname: "supp_master_name",
		title: __("Supplier Naming By"),
		description: __("By default, the supplier unique identifier is set as per the supplier name entered. If you want suppliers to be named by a set Naming Series choose the 'Naming Series' option."),
	},
	{
		fieldname: "buying_price_list",
		title: __("Default Buying Price List"),
		description: __("Configure the default Price List when creating a new purchase transaction, the default is set as 'Standard Buying'. Item prices will be fetched from this Price List.")
	},
	{
		fieldname: "po_required",
		title: __("Purchase Order Required for Purchase Invoice & Receipt Creation"),
		description: __("If this option is configured 'Yes', Dokos will prevent you from creating a Purchase Invoice or Receipt without creating a Purchase Order first. This configuration can be overridden for a particular supplier by enabling the 'Allow Purchase Invoice Creation Without Purchase Order' checkbox in supplier master.")
	},
	{
		fieldname: "pr_required",
		title: __("Purchase Receipt Required for Purchase Invoice Creation"),
		description: __("If this option is configured 'Yes', Dokos will prevent you from creating a Purchase Invoice without creating a Purchase Receipt first. This configuration can be overridden for a particular supplier by enabling the 'Allow Purchase Invoice Creation Without Purchase Receipt' checkbox in supplier master.")
	}
];