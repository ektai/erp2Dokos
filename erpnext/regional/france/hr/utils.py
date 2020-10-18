# Copyright (c) 2020, Dokos SAS and Contributors
# License: See license.txt

import frappe
import math
from frappe.utils import getdate, flt, today
from erpnext.hr.utils import get_holidays_for_employee, create_additional_leave_ledger_entry, EarnedLeaveAllocator, EarnedLeaveCalculator


def allocate_earned_leaves():
	FranceLeaveAllocator(FranceLeaveCalculator).allocate()

class FranceLeaveAllocator(EarnedLeaveAllocator):
	def __init__(self, calculator):
		super(FranceLeaveAllocator, self).__init__(calculator)

class FranceLeaveCalculator(EarnedLeaveCalculator):
	def __init__(self, parent, leave_type, allocation):
		super(FranceLeaveCalculator, self).__init__(parent, leave_type, allocation)
		self.formula_map = {
			"Congés payés sur jours ouvrables": self.conges_payes_ouvrables,
			"Congés payés sur jours ouvrés": self.conges_payes_ouvres
		}

	def conges_payes_ouvrables(self):
		self.earned_leaves = self.earneable_leaves * flt(max(round(len(self.attendance.get("dates", [])) / 24), round(self.attendance.get("weeks", 0) / 4)))
		self.allocate_earned_leaves_based_on_formula()

	def conges_payes_ouvres(self):
		self.earned_leaves = self.earneable_leaves * flt(max(round(len(self.attendance.get("dates", [])) / 20), round(self.attendance.get("weeks", 0) / 4)))
		self.allocate_earned_leaves_based_on_formula()

	def allocate_earned_leaves_based_on_formula(self):
		allocation = frappe.get_doc('Leave Allocation', self.allocation.name)
		new_allocation = flt(allocation.new_leaves_allocated) + flt(self.earned_leaves)

		if new_allocation > self.leave_type.max_leaves_allowed and self.leave_type.max_leaves_allowed > 0:
			new_allocation = self.leave_type.max_leaves_allowed

		if new_allocation == allocation.total_leaves_allocated:
			return

		if getdate(today()) >= getdate(frappe.db.get_value("Leave Period", allocation.leave_period, "to_date")):
			new_allocation = math.ceil(flt(new_allocation))

		allocation_difference = flt(new_allocation) - flt(allocation.total_leaves_allocated)

		allocation.db_set("total_leaves_allocated", new_allocation, update_modified=False)
		create_additional_leave_ledger_entry(allocation, allocation_difference, self.parent.today)

