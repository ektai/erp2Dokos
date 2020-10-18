frappe.listview_settings['Event Slot'] = {
	get_indicator: function(doc) {
		if (doc.available_bookings > doc.already_booked) {
			return [__("Slots available"), "orange"];
		} else {
			return [__("Fully booked"), "green"];
		}
	}
};