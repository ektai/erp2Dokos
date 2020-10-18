import frappe
from frappe import _

def handle_stripe_errors(func):
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Stripe Gateway Error")
	return wrapper