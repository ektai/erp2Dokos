# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

exclude_from_linked_with = True
class SubscriptionEvent(Document):
	pass


def delete_linked_subscription_events(doc):
	events = frappe.get_all("Subscription Event", filters={"document_type": doc.doctype, "document_name": doc.name}, fields=["name", "docstatus"])
	for event in events:
		if event.docstatus == 1:
			e = frappe.get_doc("Subscription Event", event.name)
			e.flags.ignore_permissions = True
			e.cancel()
