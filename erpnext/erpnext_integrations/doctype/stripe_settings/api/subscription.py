import frappe
from erpnext.erpnext_integrations.idempotency import IdempotencyKey, handle_idempotency
from erpnext.erpnext_integrations.doctype.stripe_settings.api.errors import handle_stripe_errors

class StripeSubscription:
	def __init__(self, gateway):
		self.gateway = gateway

	@handle_idempotency
	@handle_stripe_errors
	def create(self, subscription, customer, **kwargs):
		return self.gateway.stripe.Subscription.create(
			customer=customer,
			idempotency_key=IdempotencyKey("subscription", "create", subscription).get(),
			**kwargs
		)

	@handle_stripe_errors
	def retrieve(self, id):
		return self.gateway.stripe.Subscription.retrieve(
			id
		)

	@handle_stripe_errors
	def cancel(self, id, invoice_now=False, prorate=False):
		return self.gateway.stripe.Subscription.delete(
			id,
			invoice_now=invoice_now,
			prorate=prorate
		)