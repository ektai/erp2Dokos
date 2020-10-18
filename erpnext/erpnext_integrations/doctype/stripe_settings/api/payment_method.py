import frappe
from erpnext.erpnext_integrations.doctype.stripe_settings.api.errors import handle_stripe_errors

class StripePaymentMethod:
	def __init__(self, gateway):
		self.gateway = gateway

	@handle_stripe_errors
	def create(self, payment_method_type, **kwargs):
		return self.gateway.stripe.PaymentMethod.create(
			type=payment_method_type,
			**kwargs
		)

	@handle_stripe_errors
	def retrieve(self, id):
		return self.gateway.stripe.PaymentMethod.retrieve(
			id
		)

	@handle_stripe_errors
	def update(self, id, **kwargs):
		return self.gateway.stripe.PaymentMethod.modify(
			id,
			**kwargs
		)

	@handle_stripe_errors
	def attach(self, id, customer_id):
		return self.gateway.stripe.PaymentMethod.attach(
			id,
			customer=customer_id
		)

	@handle_stripe_errors
	def detach(self, id):
		return self.gateway.stripe.PaymentMethod.detach(
			id
		)

	@handle_stripe_errors
	def get_list(self, customer_id, payment_method_type="card", **kwargs):
		return self.gateway.stripe.PaymentMethod.list(
			customer=customer_id,
			type=payment_method_type,
			**kwargs
		)