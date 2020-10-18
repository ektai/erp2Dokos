from __future__ import unicode_literals
import frappe

def execute():
	frappe.reload_doc("accounts", "doctype", "POS Profile")
	frappe.db.sql(
		"""UPDATE `tabPOS Profile` profile
		SET profile.`print_format` = 'POS Invoice'
		WHERE profile.`print_format` = 'Point of Sale'""")