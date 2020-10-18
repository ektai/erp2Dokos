// Copyright (c) 2020, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ready(function(){
	new erpnext.eventSlotsBookings({
		parentId: "event-slots"
	})
})