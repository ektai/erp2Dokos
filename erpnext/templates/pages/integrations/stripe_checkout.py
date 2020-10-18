# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
from datetime import datetime
import frappe
from frappe import _
from frappe.utils import cint, fmt_money, getdate, nowdate, get_datetime
from frappe.integrations.utils import get_gateway_controller
from erpnext.erpnext_integrations.doctype.stripe_settings.api import (StripeCustomer, 
	StripePaymentMethod, StripePaymentIntent, StripeInvoice, StripeSubscription)
from erpnext.accounts.doctype.subscription.subscription_state_manager import SubscriptionPeriod

def get_context(context):
	context.no_cache = 1
	context.lang = frappe.local.lang

	if frappe.db.exists("Payment Request", {"payment_key": frappe.form_dict.get("key"), "docstatus": 1}):
		payment_request = frappe.get_doc("Payment Request", {"payment_key": frappe.form_dict.get("key")})

		if payment_request.status in ("Paid", "Completed", "Cancelled"):
			frappe.redirect_to_message(_('Already paid'), _('This payment has already been done.<br>Please contact us if you have any question.'))
			frappe.local.flags.redirect_location = frappe.local.response.location
			raise frappe.Redirect

		gateway_controller = frappe.get_doc("Stripe Settings", get_gateway_controller(payment_request.doctype, payment_request.name))

		customer_id = payment_request.get_customer()
		context.customer = StripeCustomer(gateway_controller).get_or_create(customer_id).get("id") if customer_id else ""

		context.publishable_key = gateway_controller.publishable_key
		context.payment_key = frappe.form_dict.get("key")
		context.image = gateway_controller.header_img
		context.description = payment_request.subject
		context.payer_name = frappe.db.get_value("Customer", customer_id, "customer_name") if customer_id else ""
		context.payer_email = payment_request.email_to or (frappe.session.user if frappe.session.user != "Guest" else "")
		context.amount = fmt_money(amount=payment_request.grand_total, currency=payment_request.currency)
		context.is_subscription = 1 if (payment_request.is_linked_to_a_subscription() and cint(gateway_controller.subscription_cycle_on_stripe)) else 0
		context.payment_success_redirect = gateway_controller.redirect_url or "payment-success"
		context.payment_failure_redirect = gateway_controller.failure_redirect_url or "payment-failed"

	else:
		frappe.redirect_to_message(_('Invalid link'), _('This link is not valid.<br>Please contact us.'))
		frappe.local.flags.redirect_location = frappe.local.response.location
		raise frappe.Redirect

def get_api_key(gateway_controller):
	if isinstance(gateway_controller, str):
		return frappe.get_doc("Stripe Settings", gateway_controller).publishable_key

	return gateway_controller.publishable_key

@frappe.whitelist(allow_guest=True)
def make_payment_intent(payment_key, customer):
	payment_request = frappe.get_doc("Payment Request", {"payment_key": payment_key})
	gateway_controller = get_gateway_controller("Payment Request", payment_request.name)
	payment_gateway = frappe.get_doc("Stripe Settings", gateway_controller)

	payment_intent = StripePaymentIntent(payment_gateway, payment_request).create(
		amount=(cint(payment_request.grand_total) * 100),
		currency=payment_request.currency,
		customer=customer,
		metadata={
			"reference_doctype": payment_request.reference_doctype,
			"reference_name": payment_request.reference_name,
			"payment_request": payment_request.name
		}
	)
	return payment_intent

@frappe.whitelist(allow_guest=True)
def retry_invoice(**kwargs):
	payment_request, payment_gateway = update_payment_method(**kwargs)

	invoice = StripeInvoice(payment_gateway).retrieve(kwargs.get("invoiceId"), expand=['payment_intent'])
	return invoice

@frappe.whitelist(allow_guest=True)
def make_subscription(**kwargs):
	payment_request, payment_gateway = update_payment_method(**kwargs)

	subscription = frappe.get_doc("Subscription", payment_request.is_linked_to_a_subscription())
	items = [{'price': x.stripe_plan, 'quantity': x.qty} for x in subscription.plans if x.stripe_plan and x.status == "Active"]

	data = dict(
		items=items,
		expand=['latest_invoice.payment_intent'],
		metadata={
			"reference_doctype": subscription.doctype,
			"reference_name": subscription.name
		}
	)

	if subscription.trial_period_end:
		data.update({"trial_end": int(datetime.timestamp(get_datetime(subscription.trial_period_end)))})

	if getdate(subscription.start) < getdate(nowdate()):
		data.update({
			"backdate_start_date": int(datetime.timestamp(get_datetime(subscription.start))),
			"billing_cycle_anchor": int(datetime.timestamp(get_datetime(SubscriptionPeriod(subscription).get_next_invoice_date())))
		})
	else:
		data.update({"proration_behavior": "none"})

	return StripeSubscription(payment_gateway).create(
		subscription.name,
		kwargs.get("customerId"),
		**data
	)

def update_payment_method(**kwargs):
	payment_request = frappe.get_doc("Payment Request", {"payment_key": kwargs.get("payment_key")})
	gateway_controller = get_gateway_controller("Payment Request", payment_request.name)
	payment_gateway = frappe.get_doc("Stripe Settings", gateway_controller)

	StripePaymentMethod(payment_gateway).attach(kwargs.get("paymentMethodId"), kwargs.get("customerId"))
	StripeCustomer(payment_gateway).update(kwargs.get("customerId"),
		invoice_settings={
			'default_payment_method': kwargs.get("paymentMethodId"),
		}
	)

	return payment_request, payment_gateway