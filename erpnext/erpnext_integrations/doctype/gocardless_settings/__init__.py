# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from urllib.parse import parse_qs
from gocardless_pro import webhooks as gocardless_webhooks
from gocardless_pro.errors import InvalidSignatureError

@frappe.whitelist(allow_guest=True)
def webhooks():
	r = frappe.request
	if not r:
		return

	account, events = get_events(r)
	for event in events:
		try:
			doc = create_new_integration_log(event, account)

			frappe.enqueue(method='erpnext.erpnext_integrations.doctype.gocardless_settings.gocardless_settings.handle_webhooks',\
				queue='long', timeout=600, is_async=True, **{"doctype": "Integration Request",\
				"docname":  doc.name})
		except Exception:
			frappe.log_error(frappe.get_traceback(), _("GoCardless webhooks processing error"))

	frappe.response.message = "Webhook received and event type handled"
	frappe.response.http_status_code = 200

def get_events(request):
	account, secret = get_api_key(request)
	received_signature = frappe.get_request_header("Webhook-Signature")
	payload = request.get_data()
	try:
		data = gocardless_webhooks.parse(payload, secret, received_signature)
		return account, data

	except InvalidSignatureError as e:
		frappe.log_error(e, _("GoCardless webhook error"))
	except Exception as e:
		frappe.log_error(e, _("GoCardless webhook error"))

def get_api_key(request):
	account = None
	if request.query_string:
		parsed_qs = parse_qs(frappe.safe_decode(request.query_string))
		account = parsed_qs.get("account")

		if isinstance(account, list):
			account = account[0]

	if account:
		return account, frappe.db.get_value("GoCardless Settings", account, "webhooks_secret")
	else:
		gocardless_accounts = frappe.get_all("GoCardless Settings")
		if len(gocardless_accounts) > 1:
			frappe.log_error(_("Please define your GoCardless account in the webhook URL's query string"),\
				_("GoCardless webhook error"))
		else:
			return gocardless_accounts[0].get("name"), frappe.db.get_value("GoCardless Settings", gocardless_accounts[0].get("name"), "webhooks_secret")

def create_new_integration_log(event, account):
	integration_request = frappe.get_doc({
		"doctype": "Integration Request",
		"integration_type": "Webhook",
		"integration_request_service": "GoCardless",
		"service_document": event.attributes.get("resource_type"),
		"service_status": event.attributes.get("action"),
		"service_id": event.attributes.get("id"),
		"data": json.dumps(event.attributes, indent=4),
		"payment_gateway_controller": account
	})

	integration_request.flags._name = event.attributes.get("id")

	integration_request.insert(ignore_permissions=True)
	frappe.db.commit()

	return integration_request