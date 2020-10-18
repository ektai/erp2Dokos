// Copyright (c) 2020, Dokos SAS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Event Slot', {
	onload(frm) {
		frm.email_field = "registered_emails"
	},
	refresh: function(frm) {
		frm.get_field("registered_users_html").$wrapper.html(`<div class="registered_user card-columns"></div>`);
		const $registered_wrapper = frm.get_field("registered_users_html").$wrapper.find(".registered_user");
		if (frm.doc.already_booked > 0) {
			frappe.db.get_list("Event Slot Booking", {filters: {event_slot: frm.doc.name}, fields: ["user"]})
			.then(r => {
				if (r.length) {
					r.forEach(user => {
						frappe.db.get_value("User", user.user, ["full_name", "email", "phone", "mobile_no"], res => {
							$registered_wrapper.append(`
								<div class="card" style="width: 18rem;">
									<div class="card-body">
										<h5 class="card-title">${frappe.avatar(user.user)} ${res.full_name}</h5>
										<p class="card-text"><i class="uil uil-phone-alt"></i>${res.mobile_no || __("Not available") }</p>
										<p class="card-text"><i class="uil uil-mobile-vibrate"></i>${res.phone || __("Not available") }</p>
										<p class="card-text"><i class="uil uil-at"></i>${res.email || __("Not available") }</p>
									</div>
								</div>
							`)
						})
					})
				} else {
					$registered_wrapper.html(`<p class="small text-muted">${__("No registered user")}</p>`)
				}
			})
		}
	},
	event: function(frm) {
		if (frm.doc.event && !frm.doc.starts_on) {
			frappe.db.get_value("Event", frm.doc.event, ["starts_on", "ends_on"], r => {
				frm.set_value("starts_on", r.starts_on);
				frm.set_value("ends_on", r.ends_on);
			})
		}
	}
});
