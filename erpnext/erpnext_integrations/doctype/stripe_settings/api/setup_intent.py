import frappe
from erpnext.erpnext_integrations.doctype.stripe_settings.api.errors import handle_stripe_errors

class StripeSetupIntent:
	def __init__(self, gateway):
		self.gateway = gateway

	@handle_stripe_errors
	def create(self, customer, **kwargs):
		from hashlib import sha224
		return self.gateway.stripe.SetupIntent.create(
			customer=customer,
			**kwargs
		)

	@handle_stripe_errors
	def retrieve(self, client_secret):
		return self.gateway.stripe.SetupIntent.retrieve(
			client_secret=client_secret
		)

	@handle_stripe_errors
	def update(self, id, **kwargs):
		return self.gateway.stripe.SetupIntent.modify(
			id,
			**kwargs
		)

	@handle_stripe_errors
	def confirm(self, id, **kwargs):
		return self.gateway.stripe.SetupIntent.confirm(
			id,
			**kwargs
		)

	@handle_stripe_errors
	def capture(self, id, **kwargs):
		return self.gateway.stripe.SetupIntent.attach(
			id,
			**kwargs
		)

	@handle_stripe_errors
	def cancel(self, id, **kwargs):
		return self.gateway.stripe.SetupIntent.detach(
			id,
			**kwargs
		)

	@handle_stripe_errors
	def get_list(self, **kwargs):
		return self.gateway.stripe.SetupIntent.list(
			**kwargs
		)