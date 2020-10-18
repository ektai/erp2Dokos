import frappe
from frappe import _
from hashlib import sha224
import stripe, gocardless_pro

class IdempotencyKey:
	def __init__(self, document, action, id):
		self.document = document
		self.action = action
		self.id = id

	def get(self):
		return f"{self.document}:{self.action}:{sha224(frappe.safe_encode(self.id)).hexdigest()[:30]}"


def handle_idempotency(func):
	def wrapper(*args, **kwargs):
		try:
			return func(*args, **kwargs)
		except stripe.error.IdempotencyError:
			frappe.throw(_("This request has already been completed within the last 24 hours.<br> Please contact us for any question."))
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Payment Gateway Error")
	return wrapper
