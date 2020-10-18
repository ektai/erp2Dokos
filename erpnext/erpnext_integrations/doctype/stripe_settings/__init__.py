# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import json
import stripe
from urllib.parse import parse_qs

TEST_EVENT_ID = "evt_00000000000000"

@frappe.whitelist(allow_guest=True)
def webhooks():
	r = frappe.request
	payload = json.loads(r.get_data()) or []
	if not payload:
		frappe.response.message = "Missing payload"
		frappe.response.http_status_code = 400

	account, stripe_key = get_api_key(r)
	webhook_secret = frappe.get_request_header("HTTP_STRIPE_SIGNATURE")

	event = None
	try:
		event = stripe.Event.construct_from(
			payload, webhook_secret, stripe_key
		)
	except Exception as e:
		frappe.response.message = "Webhook event construction failed"
		frappe.response.http_status_code = 400

	# Handle the event
	doc = create_new_integration_log(event, account)

	frappe.enqueue(method='erpnext.erpnext_integrations.doctype.stripe_settings.stripe_settings.handle_webhooks',\
		queue='long', timeout=600, is_async=True, **{"doctype": "Integration Request",\
		"docname":  doc.name})

	frappe.response.message = "Webhook received and event type handled"
	frappe.response.http_status_code = 200

def get_api_key(request):
	account = None
	if request.query_string:
		parsed_qs = parse_qs(frappe.safe_decode(request.query_string))
		account = parsed_qs.get("account")

		if isinstance(account, list):
			account = account[0]

	if account:
		return account, frappe.get_doc("Stripe Settings", account).get_password(\
			fieldname="secret_key", raise_exception=False)
	else:
		stripe_accounts = frappe.get_all("Stripe Settings")
		if len(stripe_accounts) > 1:
			frappe.log_error(_("Please define your Stripe account in the webhook URL's query string"),\
				_("Stripe webhook error"))
		else:
			return stripe_accounts[0].get("name"), frappe.get_doc("Stripe Settings", stripe_accounts[0].get("name")).get_password(\
				fieldname="secret_key", raise_exception=False)

def create_new_integration_log(event, account):
	integration_request = frappe.get_doc({
		"doctype": "Integration Request",
		"integration_type": "Webhook",
		"integration_request_service": "Stripe",
		"service_document": event.type.split(".")[0],
		"service_status": event.type.split(".")[1],
		"service_id": event.data.object.get("id"),
		"data": json.dumps(event, indent=4),
		"payment_gateway_controller": account
	})

	if event.id != TEST_EVENT_ID:
		integration_request.flags._name = event.id

	integration_request.insert(ignore_permissions=True)
	frappe.db.commit()

	return integration_request
