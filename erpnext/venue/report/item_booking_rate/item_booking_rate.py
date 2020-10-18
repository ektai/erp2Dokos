# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, flt, formatdate
from collections import defaultdict, Counter
import calendar
import datetime
from erpnext.accounts.dashboard_chart_source.account_balance_timeline.account_balance_timeline import get_dates_from_timegrain
from erpnext.venue.doctype.item_booking.item_booking import get_item_calendar

def execute(filters=None):
	dates = get_dates_from_timegrain(filters.get("date_range")[0], filters.get("date_range")[1], filters.get("period"))
	data, chart = get_data(filters, dates)
	columns = get_columns(filters, dates)
	return columns, data, [], chart


def get_data(filters, dates):

	if not filters.get("date_range"):
		return []

	status_filter = "Confirmed, Not Confirmed" if filters.get("status") == "Confirmed and not confirmed" else "Confirmed"

	item_booking = frappe.get_all("Item Booking",
		filters={"starts_on": ("between", filters.get("date_range")), "status": ("in", (f"{status_filter}"))},
		fields=["status", "name", "item", "item_name", "starts_on", "ends_on"])

	items_dict = defaultdict(lambda: defaultdict(float))
	sorted_dates = sorted(dates)

	# Get minutes booked
	for ib in item_booking:
		ib["diff_minutes"] = (ib.get("ends_on") - ib.get("starts_on")).total_seconds() / 60.0
		closest = None

		for date in sorted_dates:
			if closest is None and getdate(ib.get("starts_on")) <= getdate(date):
				closest = date

		items_dict[ib["item"]]["item_name"] = ib["item_name"]
		items_dict[ib["item"]][frappe.scrub(str(closest))] += flt(ib["diff_minutes"]) / 60.0
		items_dict[ib["item"]]["total"] += flt(ib["diff_minutes"]) / 60.0

	get_calendar_capacity(filters, items_dict, sorted_dates)

	output = [{"item": x, **items_dict[x]} for x in items_dict]

	for date in dates:
		output = [{f"{frappe.scrub(str(date))}_percent": (flt(x.get(frappe.scrub(str(date)))) / flt(x[f"{frappe.scrub(str(date))}_capacity"] or 1) * 100), **x} for x in output]

	scrubed_dates = [frappe.scrub(str(date)) for date in dates]

	for line in output:
		line["capacity"] = sum([line.get(x) for x in line if x.endswith("_capacity")])

	chart_data = get_chart_data(output)

	return output, chart_data

def get_calendar_capacity(filters, items, dates):
	for item in items:
		daily_capacity = defaultdict(float)
		calendar = get_item_calendar(item)
		for line in calendar.get("calendar"):
			daily_capacity[line.day] += (line.get("end_time") - line.get("start_time")).total_seconds() / 3600

		prev_date = filters.get("date_range")[0]
		for date in dates:
			next_date = min(getdate(date), getdate(filters.get("date_range")[1]))
			weekdays = dict(count_weekday(prev_date, next_date))
			items[item][f"{frappe.scrub(str(date))}_capacity"] = sum([daily_capacity[x] * weekdays[x[:3]] for x in daily_capacity if x[:3] in weekdays])
			prev_date = date


def dates_between(start, end):
	while start <= end:
		yield start
		start += datetime.timedelta(1)

def count_weekday(start, end):
	counter = Counter()
	for date in dates_between(getdate(start), getdate(end)):
		counter[date.strftime('%a')] += 1
	return counter


def get_columns(filters, dates):
	columns = [
		{
			"label": _("Item"),
			"fieldtype": "Link",
			"fieldname": "item",
			"options": "Item",
			"width": 180
		},
		{
			"label": _("Item Name"),
			"fieldtype": "Data",
			"fieldname": "item_name",
			"width": 250
		}
	]

	for date in dates:
		columns.extend([
			{
				"label": _("Hours Booked") + " - " + formatdate(date),
				"fieldtype": "Int",
				"fieldname": frappe.scrub(str(date)),
				"width": 250
			},
			{
				"label": _("Booking rate") + " - " + formatdate(date),
				"fieldtype": "Percent",
				"fieldname": frappe.scrub(str(date)) + "_percent",
				"width": 250
			}
		])

	return columns


def get_chart_data(data):
	return {
		"data" : {
			"labels" : [x.get("item_name") for x in data],
			"datasets" : [
				{
					"name" : _("Capacity (Hours)"),
					"values" : [round(x.get("capacity"), 2) for x in data]
				},
				{
					"name" : _("Bookings (Hours)"),
					"values" : [round(x.get("total"), 2) for x in data]
				}
			]
		},
		"type" : "bar"
	}