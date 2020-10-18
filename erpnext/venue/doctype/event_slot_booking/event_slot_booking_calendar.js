// Copyright (c) 2020, Dokos SAS and Contributors
// License: See license.txt

frappe.views.calendar["Event Slot Booking"] = {
	field_map: {
		"start": "starts_on",
		"end": "ends_on",
        "id": "name",
        "title": "user_name",
        "description": "slot_title"
    },
    no_all_day: true
};