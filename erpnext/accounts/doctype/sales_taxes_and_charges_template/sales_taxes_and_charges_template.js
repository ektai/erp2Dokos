// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.cscript.tax_table = "Sales Taxes and Charges";

{% include "erpnext/public/js/controllers/accounts.js" %}

frappe.tour['Sales Taxes and Charges Template'] = [
	{
		fieldname: "title",
		title: __("Title"),
		description: __("The template's title. Should help you find it in transaction."),
	},
	{
		fieldname: "is_default",
		title: __("Default template"),
		description: __("Should be checked if this template is your default template."),
	},
	{
		fieldname: "disabled",
		title: __("Disabled"),
		description: __("Should be checked if this template is disabled"),
	},
	{
		fieldname: "company",
		title: __("Company"),
		description: __("The company this template should apply to."),
	},
	{
		fieldname: "tax_category",
		title: __("Tax category"),
		description: __("The tax category this template is linked to, if applicable."),
	},
	{
		fieldname: "taxes",
		title: __("Taxes and charges table"),
		description: __("Each line represents a different rule to be applied to your transactions."),
	}
]