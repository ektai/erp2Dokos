frappe.listview_settings['Subscription'] = {
	get_indicator: function(doc) {
		if(doc.status === 'Trial') {
			return [__("Trial"), "blue"];
		} else if(doc.status === 'Active') {
			return [__("Active"), "blue"];
		} else if(doc.status === 'Unpaid') {
			return [__(doc.status), "red"];
		} else if(doc.status === 'Paid') {
			return [__("Paid"), "green"];
		} else if(doc.status === 'Cancelled') {
			return [__("Cancelled"), "darkgray"];
		} else if(doc.status === 'Billable') {
			return [__("Billable"), "orange"];
		} else if(doc.status === 'Billing failed') {
			return [__("Billing failed"), "red"];
		} else if(doc.status === 'Payable') {
			return [__("Payable", null, "Subscription"), "orange"];
		} else if(doc.status === 'Draft invoices') {
			return [__("Draft invoices"), "orange"];
		}
	}
};
