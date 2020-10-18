# -*- coding: utf-8 -*-
# Copyright (c) 2019, Dokos SAS and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.permissions import get_doctypes_with_read
import json
from frappe import _
from frappe.email.doctype.notification.notification import get_context

class AccountingJournal(Document):
	def validate(self):
		if self.conditions:
			self.validate_conditions()

	def validate_conditions(self):
		for condition in self.conditions:
			if condition.condition:
				temp_doc = frappe.new_doc(condition.document_type)
				try:
					frappe.safe_eval(condition.condition, None, get_context(temp_doc))
				except Exception:
					frappe.throw(_("The Condition '{0}' is invalid").format(condition))
