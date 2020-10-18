import frappe
from erpnext.erpnext_integrations.doctype.stripe_settings.api.errors import handle_stripe_errors

class StripePrice:
	def __init__(self, gateway):
		self.gateway = gateway

	@handle_stripe_errors
	def retrieve(self, id):
		return self.gateway.stripe.Price.retrieve(
			id
		)