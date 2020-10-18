# -*- coding: utf-8 -*-
# Copyright (c) 2019, Dokos SAS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import warnings
import frappe
from frappe import _
from urllib.parse import urlencode
from frappe.utils import get_url, call_hook_method, cint, flt, getdate, nowdate
from frappe.integrations.utils import PaymentGatewayController, create_request_log, create_payment_gateway
from erpnext.erpnext_integrations.doctype.stripe_settings.webhook_events import (StripeChargeWebhookHandler, 
	StripePaymentIntentWebhookHandler, StripeInvoiceWebhookHandler)
from erpnext.erpnext_integrations.doctype.stripe_settings.api import StripePrice
from erpnext.accounts.doctype.subscription.subscription_state_manager import SubscriptionPeriod
import stripe
import json

class StripeSettings(PaymentGatewayController):
	currency_wise_minimum_charge_amount = {
		'JPY': 50, 'MXN': 10, 'DKK': 2.50, 'HKD': 4.00, 'NOK': 3.00, 'SEK': 3.00,
		'USD': 0.50, 'AUD': 0.50, 'BRL': 0.50, 'CAD': 0.50, 'CHF': 0.50, 'EUR': 0.50,
		'GBP': 0.30, 'NZD': 0.50, 'SGD': 0.50
	}

	def __init__(self, *args, **kwargs):
		super(StripeSettings, self).__init__(*args, **kwargs)
		if not self.is_new():
			self.configure_stripe()

	def configure_stripe(self):
		self.stripe = stripe
		self.stripe.api_key = self.get_password(fieldname="secret_key", raise_exception=False)
		self.stripe.default_http_client = stripe.http_client.RequestsClient()

	def get_supported_currencies(self):
		account = self.stripe.Account.retrieve()
		supported_payment_currencies = self.stripe.CountrySpec.retrieve(account["country"])[
			"supported_payment_currencies"
		]

		return [currency.upper() for currency in supported_payment_currencies]

	def on_update(self):
		create_payment_gateway('Stripe-' + self.gateway_name, settings='Stripe Settings', controller=self.gateway_name)
		call_hook_method('payment_gateway_enabled', gateway='Stripe-' + self.gateway_name)
		if not self.flags.ignore_mandatory:
			self.validate_stripe_credentials()

	def validate_stripe_credentials(self):
		try:
			self.configure_stripe()
			balance = self.stripe.Balance.retrieve()
			return balance
		except Exception as e:
			frappe.throw(_("Stripe connection could not be initialized.<br>Error: {0}").format(str(e)))

	def validate_transaction_currency(self, currency):
		if currency not in self.get_supported_currencies():
			frappe.throw(_("Please select another payment method. Stripe does not support transactions in currency '{0}'").format(currency))

	def validate_minimum_transaction_amount(self, currency, amount):
		if currency in self.currency_wise_minimum_charge_amount:
			if flt(amount) < self.currency_wise_minimum_charge_amount.get(currency, 0.0):
				frappe.throw(_("For currency {0}, the minimum transaction amount should be {1}").format(currency,
					self.currency_wise_minimum_charge_amount.get(currency, 0.0)))

	def validate_payment_request(self, payment_request):
		subscription = payment_request.get_linked_subscription()
		if not subscription:
			return

		self.validate_subscription_lines(subscription)
		self.validate_next_invoice_date(subscription)

	def validate_subscription_lines(self, subscription):
		total = 0
		for plan in subscription.plans:
			if plan.stripe_plan:
				p = self.get_stripe_plan(plan.stripe_plan, subscription.currency)
				total += flt(p.unit_amount) / 100
			elif plan.stripe_invoice_item:
				i = self.get_stripe_invoice_item(plan.stripe_invoice_item, subscription.currency)
				total += flt(i.price.unit_amount) / 100

		if total != subscription.total:
			frappe.msgprint(_("The total billed by Stripe ({0}) will be different from the total in your subscription ({1}).").format(total, subscription.total))

	def get_stripe_plan(self, plan, currency):
		try:
			stripe_plan = StripePrice(self).retrieve(plan)
			if not stripe_plan.active:
				frappe.throw(_("Payment plan {0} is no longer active.").format(plan))
			if not currency == stripe_plan.currency.upper():
				frappe.throw(_("Payment plan {0} is in currency {1}, not {2}.")\
					.format(plan, stripe_plan.currency.upper(), currency))
			return stripe_plan
		except stripe.error.InvalidRequestError as e:
			frappe.throw(_("Invalid Stripe plan or currency: {0} - {1}").format(plan, currency))

	def get_stripe_invoice_item(self, item, currency):
			try:
				invoice_item = StripeInvoiceItem(self).retrieve(item)
				if not currency == invoice_item.currency.upper():
					frappe.throw(_("Payment plan {0} is in currency {1}, not {2}.")\
						.format(item, invoice_item.currency.upper(), currency))
				return invoice_item
			except stripe.error.InvalidRequestError as e:
				frappe.throw(_("Invalid currency for invoice item: {0} - {1}").format(item, currency))

	def validate_next_invoice_date(self, subscription):
		next_invoice_date = SubscriptionPeriod(subscription).get_next_invoice_date()
		if getdate(next_invoice_date) < getdate(nowdate()):
			frappe.throw(_("The next invoice date for this subscription is in the past and can not be billed with Stripe."))

	def get_payment_url(self, **kwargs):
		payment_key = {"key": kwargs.get("payment_key")}
		return get_url("./integrations/stripe_checkout?{0}".format(urlencode(kwargs) if not kwargs.get("payment_key") else urlencode(payment_key)))

	def cancel_subscription(self, **kwargs):
		from erpnext.erpnext_integrations.doctype.stripe_settings.api import StripeSubscription
		return StripeSubscription(self).cancel(
			kwargs.get("subscription"),
			invoice_now=kwargs.get("invoice_now", False),
			prorate=kwargs.get("prorate", False)
		)

def handle_webhooks(**kwargs):
	from erpnext.erpnext_integrations.webhooks_controller import handle_webhooks as _handle_webhooks

	WEBHOOK_HANDLERS = {
		"charge": StripeChargeWebhookHandler,
		"payment_intent": StripePaymentIntentWebhookHandler,
		"invoice": StripeInvoiceWebhookHandler
	}

	_handle_webhooks(WEBHOOK_HANDLERS, **kwargs)
