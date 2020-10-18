frappe.listview_settings['Project'] = {
	add_fields: ["status", "priority", "is_active", "percent_complete", "expected_end_date", "project_name"],
	filters:[["status","=", "Open"]],
	get_indicator: function(doc) {
		if (doc.status=="Open" && doc.percent_complete) {
			return [__("{0}%", [cint(doc.percent_complete)]), "orange", "percent_complete,>,0|status,=,Open"];
		} else if (doc.status=="Open") {
			return [__(doc.status), "green", "status,=," + doc.status];
		} else if (doc.status=="Completed") {
			return [__(doc.status), "darkgray", "status,=," + doc.status];
		} else if (doc.status=="Cancelled") {
			return [__(doc.status), "gray", "status,=," + doc.status];
		} else {
			return [__(doc.status), frappe.utils.guess_colour(doc.status), "status,=," + doc.status];
		}
	}
};
