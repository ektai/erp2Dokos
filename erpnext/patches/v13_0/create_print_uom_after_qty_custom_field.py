import frappe
from erpnext.setup.install import create_print_uom_after_qty_custom_field

def execute():
	create_print_uom_after_qty_custom_field()
