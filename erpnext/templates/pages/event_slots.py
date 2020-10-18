# Copyright (c) 2020, Dokos SAS and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _

def get_context(context):
	context.no_cache = 1
	context.show_sidebar = True
	context.no_breadcrumbs = True
	context.title = _("Event Slots")

	if frappe.session.user == "Guest":
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)