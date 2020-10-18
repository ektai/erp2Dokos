import frappe
from erpnext.erpnext_integrations.idempotency import IdempotencyKey, handle_idempotency
from erpnext.erpnext_integrations.doctype.stripe_settings.api.errors import handle_stripe_errors

class StripeInvoice:
	def __init__(self, gateway):
		self.gateway = gateway

	@handle_idempotency
	@handle_stripe_errors
	def create(self, payment_request, customer, **kwargs):
		from hashlib import sha224
		return self.gateway.stripe.Invoice.create(
			customer=customer,
			idempotency_key=IdempotencyKey("invoice", "create", payment_request).get(),
			**kwargs
		)

	@handle_stripe_errors
	def retrieve(self, id):
		return self.gateway.stripe.Invoice.retrieve(
			id
		)