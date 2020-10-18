# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from erpnext.setup.utils import insert_record

def setup_venue():
    disable_desk_access_for_volunteer_role()

def disable_desk_access_for_volunteer_role():
	try:
		volunteer_role = frappe.get_doc("Role", "Volunteer")
	except frappe.DoesNotExistError:
		create_volunteer_role()
		return

	volunteer_role.desk_access = 0
	volunteer_role.save()

def create_volunteer_role():
	volunteer_role = frappe.get_doc({
		"doctype": "Role",
		"role_name": "Volunteer",
		"desk_access": 0,
		"restrict_to_domain": "Venue"
	})
	volunteer_role.insert()