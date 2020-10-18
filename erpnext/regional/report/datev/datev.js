frappe.query_reports["DATEV"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company") || frappe.defaults.get_global_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"default": frappe.datetime.month_start(),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"default": frappe.datetime.now_date(),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "voucher_type",
			"label": __("Voucher Type"),
			"fieldtype": "Select",
			"options": "\nSales Invoice\nPurchase Invoice\nPayment Entry\nExpense Claim\nPayroll Entry\nBank Reconciliation\nAsset\nStock Entry"
		}
	],
	onload: function(query_report) {
		query_report.page.add_menu_item(__("Download DATEV File"), () => {
			const filters = JSON.stringify(query_report.get_values());
			window.open(`/api/method/erpnext.regional.report.datev.datev.download_datev_csv?filters=${filters}`);
		});
	}
};