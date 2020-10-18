# Copyright (c) 2020, Dokos SAS and Contributors
# License: See license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import fmt_money
from frappe.integrations.utils import get_gateway_controller
from frappe.utils import get_url
from frappe.contacts.doctype.contact.contact import get_default_contact

def get_context(context):
	context.no_cache = 1

	# all these keys exist in form_dict
	if frappe.db.exists("Payment Request", {"payment_key": frappe.form_dict.get("key"), "docstatus": 1}):
		payment_request = frappe.get_doc("Payment Request", {"payment_key": frappe.form_dict.get("key")})

		if payment_request.status in ("Paid", "Completed", "Cancelled"):
			frappe.redirect_to_message(_('Already paid'), _('This payment has already been done.<br>Please contact us if you have any question.'))
			frappe.local.flags.redirect_location = frappe.local.response.location
			raise frappe.Redirect

		gateway_controller = frappe.get_doc("GoCardless Settings", get_gateway_controller(payment_request.doctype, payment_request.name))
		success_url = get_url(f"./integrations/gocardless_confirmation?reference_doctype={payment_request.doctype}&reference_docname={payment_request.name}")

		try:
			redirect_flow = gateway_controller.client.redirect_flows.create(params={
				"description": _("Pay {0}").format(fmt_money(amount=payment_request.grand_total, currency=payment_request.currency)),
				"session_token": payment_request.name,
				"success_redirect_url": success_url,
				"prefilled_customer": PrefilledCustomer(payment_request).get(),
				"metadata": {
					"reference_doctype": payment_request.reference_doctype,
					"reference_name": payment_request.reference_name,
					"payment_request": payment_request.name
				}
			})

			frappe.local.flags.redirect_location = redirect_flow.redirect_url
		except Exception as e:
			print(frappe.get_traceback())
			frappe.log_error(e, "GoCardless Payment Error")
			frappe.local.flags.redirect_location = 'payment-failed'
			raise frappe.Redirect

		raise frappe.Redirect

	else:
		frappe.redirect_to_message(_('Invalid link'), _('This link is not valid.<br>Please contact us.'))
		frappe.local.flags.redirect_location = frappe.local.response.location
		raise frappe.Redirect

class PrefilledCustomer:
	def __init__(self, payment_request):
		self.payment_request = payment_request
		self.reference = frappe.get_doc(payment_request.reference_doctype, payment_request.reference_name)
		self.customer = frappe.get_doc("Customer", self.reference.customer)
		self.customer_address = {}
		self.primary_contact = {}

	def get(self):
		self.get_customer_address()
		self.get_primary_contact()

		return {
			"company_name": self.customer.customer_name,
			"given_name": self.primary_contact.get("first_name") or "",
			"family_name": self.primary_contact.get("last_name") or "",
			"email": self.primary_contact.get("email_id") or self.payment_request.email_to or frappe.session.user,
			"address_line1": self.customer_address.address_line1 or "",
			"address_line2": self.customer_address.address_line2 or "",
			"city": self.customer_address.city or "",
			"postal_code": self.customer_address.pincode or "",
			"country_code": frappe.db.get_value("Country", self.customer_address.country, "code") or ""
		}

	def get_customer_address(self):
		customer_address_name = None
		if self.reference.doctype == "Subscription":
			customer_address_name = frappe.db.get_value("Customer", self.customer.name, "customer_primary_address")
		else:
			customer_address_name = self.reference.customer_address

		self.customer_address = frappe.get_doc("Address", customer_address_name) if customer_address_name else frappe._dict()

	def get_primary_contact(self):
		if self.customer.customer_primary_contact:
			self.primary_contact = frappe.db.get_value("Contact", self.customer.customer_primary_contact,
				["first_name", "last_name", "email_id"], as_dict=True)
		else:
			get_default_contact(self.customer.doctype, self.customer.name)
