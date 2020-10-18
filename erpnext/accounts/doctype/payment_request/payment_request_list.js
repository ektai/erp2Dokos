frappe.listview_settings['Payment Request'] = {
	add_fields: ["status"],
	get_indicator: function(doc) {
		if(doc.status == "Draft") {
			return [__("Draft"), "darkgray", "status,=,Draft"];
		}
		else if(doc.status == "Initiated") {
			return [__("Initiated"), "green", "status,=,Initiated"];
		}
		else if(doc.status == "Paid") {
			return [__("Paid"), "blue", "status,=,Paid"];
		}
		else if(doc.status == "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		}
		else if(doc.status == "Pending") {
			return [__("Pending"), "orange", "status,=,Pending"];
		}
		else if(doc.status == "Failed") {
			return [__("Failed"), "orange", "status,=,Failed"];
		}
		else if(doc.status == "Completed") {
			return [__("Completed"), "blue", "status,=,Completed"];
		}
	}	
}
