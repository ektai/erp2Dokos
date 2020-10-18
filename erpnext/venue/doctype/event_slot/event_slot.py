# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

from collections import Counter 

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, global_date_format, format_time, cint

class EventSlot(Document):
	def validate(self):
		self.validate_dates()
		self.update_dates_in_bookings()

	def validate_dates(self):
		start, end = frappe.db.get_value("Event", self.event, ["starts_on", "ends_on"])
		if get_datetime(self.starts_on) < get_datetime(start):
			frappe.throw(_("The start time cannot be before {0}").format(global_date_format(get_datetime(start)) + ' ' + format_time(get_datetime(start))))

		if get_datetime(self.ends_on) > get_datetime(end):
			frappe.throw(_("The end time cannot be after {0}").format(global_date_format(get_datetime(end)) + ' ' + format_time(get_datetime(end))))

		if get_datetime(self.starts_on) > get_datetime(self.ends_on):
			frappe.throw(_("The end time must be greater than the start time"))

	def update_dates_in_bookings(self):
		doc_before_save = self.get_doc_before_save()
		for field in ("starts_on", "ends_on"):
			if not doc_before_save or (doc_before_save and getattr(doc_before_save, field, None) != getattr(self, field, None)):
				for d in frappe.get_all("Event Slot Booking", filters={"event_slot": self.name}):
					frappe.db.set_value("Event Slot Booking", d.name, field, getattr(self, field, None))

def _get_slots(start, end, filters=None, conditions=None):
	return frappe.db.sql("""
		select
			`tabEvent Slot`.name,
			`tabEvent Slot`.slot_title,
			`tabEvent Slot`.starts_on,
			`tabEvent Slot`.ends_on,
			`tabEvent Slot`.available_bookings,
			`tabEvent Slot`.description
		from
			`tabEvent Slot`
		WHERE (
				(
					(date(`tabEvent Slot`.starts_on) BETWEEN date(%(start)s) AND date(%(end)s))
					OR (date(`tabEvent Slot`.ends_on) BETWEEN date(%(start)s) AND date(%(end)s))
					OR (
						date(`tabEvent Slot`.starts_on) <= date(%(start)s)
						AND date(`tabEvent Slot`.ends_on) >= date(%(end)s)
					)
				)
			)
			{conditions}
		""".format(conditions=conditions or ""), {
			"start": start,
			"end": end
		}, as_dict=True)

@frappe.whitelist()
def get_available_slots(start, end):
	slots = _get_slots(start, end)
	slots_names = [x.get("name") for x in slots]

	booked_slots = frappe.get_all("Event Slot Booking", filters={"event_slot": ("in", slots_names)}, fields=["event_slot", "user"])
	booking_count = Counter([x.event_slot for x in booked_slots])

	return [dict(
		start=x.starts_on,
		end=x.ends_on,
		id=x.name,
		title=x.slot_title,
		description=get_formatted_description(x, booked_slots, cint(booking_count.get(x.name))),
		content=x.description,
		available_slots=cint(x.available_bookings),
		booked_slots=cint(booking_count.get(x.name)),
		booked_by_user=bool([y.user == frappe.session.user for y in booked_slots if y.event_slot == x.name]),
		textColor='#fff',
		display='background' if cint(booking_count.get(x.name)) >= cint(x.available_bookings) else None,
		backgroundColor='#3788d8' if cint(booking_count.get(x.name)) >= cint(x.available_bookings) else get_color(x, booked_slots, booking_count),
	) for x in slots]

def get_formatted_description(slot, booked_slots, booked_number):
	remaining_slots = max(0, cint(slot.available_bookings) - booked_number)
	booked_by_user = bool([x.user == frappe.session.user for x in booked_slots if x.event_slot == slot.name])
	html = f"""
		<p class="card-text">🡒 {remaining_slots} {_("slot available") if remaining_slots in (0, 1) else _("slots available")}</p>
	"""

	if booked_by_user:
		html += f"""
			<p>🡒 {_("You are registered")}</p>
		"""

	return f"""
		<div>
			<h6 class="card-title text-white">{slot.slot_title}</h6>
			{html}
		</div>
	"""

def get_color(slot, booked_slots, booking_count):
	booked_by_user = bool([x.user == frappe.session.user for x in booked_slots if x.event_slot == slot.name])
	if cint(slot.available_bookings) <= cint(booking_count.get(slot.name)):
		return "gray"
	elif booked_by_user:
		return "#3788d8"
	else:
		return "green"