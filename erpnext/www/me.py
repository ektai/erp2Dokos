# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
import frappe.www.list
from erpnext.controllers.website_list_for_contact import get_customers_suppliers
from erpnext.templates.pages.integrations.stripe_checkout import get_api_key

from erpnext.erpnext_integrations.doctype.stripe_settings.api import StripePaymentMethod

no_cache = 1

def get_context(context):
	if frappe.session.user=='Guest':
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

	context.show_sidebar = True
	context.enable_stripe = False
	context.enable_gocardless = False
	context.subscription = False
	context.subscriptions_available = False
	context.lang = frappe.local.lang

	active_tokens = frappe.get_all("OAuth Bearer Token",\
		filters=[["user", "=", frappe.session.user]],\
		fields=["client"], distinct=True, order_by="creation")
	context.third_party_apps = True if active_tokens else False

	customers, suppliers = get_customers_suppliers("Integration References", frappe.session.user)
	if customers:
		if frappe.db.exists("Integration References", dict(customer=customers[0])):
			references = frappe.get_doc("Integration References", dict(customer=customers[0]))
			if references.get("stripe_customer_id") and references.get("stripe_settings"):
				context.enable_stripe = True
				context.stripe_payment_methods = get_customer_payment_methods(references)
				context.publishable_key = get_api_key(references.stripe_settings)

		if frappe.db.exists("Subscription", {"customer": customers[0]}):
			context.subscription = frappe.get_doc("Subscription", {"customer": customers[0]})

		context.subscriptions_available = True if frappe.db.get_value("Subscription Template", {"enable_on_portal": 1}) else False

def get_customer_payment_methods(references):
	try:
		stripe_settings = frappe.get_doc("Stripe Settings", references.stripe_settings)
		return StripePaymentMethod(stripe_settings).get_list(references.stripe_customer_id)
	except Exception:
		frappe.log_error(frappe.get_traceback(),\
			_("[Portal] Stripe payment methods retrieval error for {0}").format(references.customer))

@frappe.whitelist()
def remove_payment_card(id):
	try:
		customers, suppliers = get_customers_suppliers("Integration References", frappe.session.user)
		account = frappe.get_doc("Integration References", dict(customer=customers[0]))
		if account.stripe_settings:
			stripe_settings = frappe.get_doc("Stripe Settings", account.stripe_settings)
			return StripePaymentMethod(stripe_settings).detach(id, account.stripe_customer_id)

	except Exception:
		frappe.log_error(frappe.get_traceback(), _("[Portal] Stripe payment source deletion error"))

@frappe.whitelist()
def add_new_payment_card(payment_method):
	try:
		customers, suppliers = get_customers_suppliers("Integration References", frappe.session.user)
		account = frappe.get_doc("Integration References", dict(customer=customers[0]))
		if account.stripe_settings:
			stripe_settings = frappe.get_doc("Stripe Settings", account.stripe_settings)
			return StripePaymentMethod(stripe_settings).attach(payment_method, account.stripe_customer_id)

	except Exception:
		frappe.log_error(frappe.get_traceback(), _("[Portal] New stripe payment source registration error"))
