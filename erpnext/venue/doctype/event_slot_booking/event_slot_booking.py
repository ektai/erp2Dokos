# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint
from frappe.model.document import Document

class EventSlotBooking(Document):
	def validate(self):
		self.check_slots_number()

	def on_update(self):
		self.update_slot()

	def after_delete(self):
		self.update_slot()

	def check_slots_number(self):
		slots_limit = frappe.db.get_value("Event Slot", self.event_slot, "available_bookings")

		if (len(frappe.get_all("Event Slot Booking", filters={"event_slot": self.event_slot})) + 1) > slots_limit:
			frappe.throw(_("Only {0} users can be booked against this event slot").format(cint(slots_limit)))

	def update_slot(self):
		users = [x.user for x in frappe.get_all("Event Slot Booking", filters={"event_slot": self.event_slot}, fields=["user"])]
		frappe.db.set_value("Event Slot", self.event_slot, "already_booked", len(users))
		frappe.db.set_value("Event Slot", self.event_slot, "registered_emails", ",".join(users) if users else "")


@frappe.whitelist()
def register_for_slot(slot, user=None):
	frappe.get_doc({
		"doctype": "Event Slot Booking",
		"event_slot": slot,
		"user": user or frappe.session.user
	}).insert(ignore_permissions=True)