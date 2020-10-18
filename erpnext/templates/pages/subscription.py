# Copyright (c) 2020, Dokos SAS and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

from frappe import _
from frappe.utils import nowdate, cint, get_url
from erpnext.controllers.website_list_for_contact import get_customers_suppliers
from erpnext.accounts.doctype.subscription_template.subscription_template import make_subscription
from erpnext.shopping_cart.cart import get_party
from erpnext.accounts.doctype.payment_request.payment_request import get_payment_link
from erpnext.accounts.doctype.subscription.subscription_state_manager import SubscriptionPeriod

def get_context(context):
	context.no_cache = 1
	context.show_sidebar = True

	if not cint(frappe.db.get_single_value("Shopping Cart Settings", "enabled")) \
		or frappe.session.user == "Guest":
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

@frappe.whitelist()
def get_subscription_context():
	subscription = None
	subscription_plans = []
	customer_groups = [""]

	customers, suppliers = get_customers_suppliers("Integration References", frappe.session.user)
	if customers:
		customer_groups.append(frappe.db.get_value("Customer", customers[0], "customer_group"))
		if frappe.db.exists("Subscription", {"customer": customers[0]}):
			subscription = frappe.get_doc("Subscription", {"customer": customers[0]})

	plans = frappe.get_all("Subscription Plan", filters={"enable_on_portal": 1, "customer_group": ("in", customer_groups)})
	for plan in plans:
		subscription_plans.append(
			frappe.get_doc("Subscription Plan", plan.name)
		)

	return {
		"subscription": subscription,
		"subscription_plans": subscription_plans,
		"available_subscriptions": frappe.get_all("Subscription Template", filters={"enable_on_portal": 1}, fields=["*"]),
		"next_invoice_date": subscription.get_next_invoice_date() if subscription else ""
	}

@frappe.whitelist()
def get_subscription_table(subscription):
	doc = frappe.get_doc("Subscription", subscription)
	return frappe.render_template("templates/includes/subscription_table.html", {"subscription": doc})

@frappe.whitelist()
def add_plan(subscription, plan):
	subscription = frappe.get_doc("Subscription", subscription)
	subscription.add_plan(plan)
	return subscription.save(ignore_permissions=True)

@frappe.whitelist()
def remove_subscription_line(subscription, line):
	subscription = frappe.get_doc("Subscription", subscription)
	subscription.remove_plan(line)
	return subscription.save(ignore_permissions=True)

@frappe.whitelist()
def new_subscription(template):
	customer = None
	customers, suppliers = get_customers_suppliers("Integration References", frappe.session.user)
	customer = customers[0] if customers else get_party().name

	company = frappe.db.get_single_value("Shopping Cart Settings", "company")

	subscription = make_subscription(template=template, company=company, customer=customer, start_date=nowdate(), ignore_permissions=True)
	payment_key = frappe.db.get_value("Payment Request", {"reference_doctype": "Subscription", "reference_name": subscription.name, "status": "Initiated"}, "payment_key")
	
	return {
		"subscription": subscription,
		"payment_link": get_url("/payments?link={0}".format(payment_key)) if payment_key else None
	}

@frappe.whitelist()
def cancel_subscription(subscription):
	subscription = frappe.get_doc("Subscription", subscription)
	subscription.cancellation_date = subscription.current_invoice_end
	return subscription.save(ignore_permissions=True)

@frappe.whitelist()
def get_payment_requests(subscription):
	output = []
	payment_requests = frappe.get_all("Payment Request", filters={
		"docstatus": 1,
		"reference_doctype": "Subscription",
		"reference_name": subscription,
		"status": "Initiated"
	}, fields=["name", "payment_key", "grand_total"])

	if payment_requests:
		output = [dict(x, **{"payment_link": get_payment_link(x.payment_key)}) for x in payment_requests]

	return output

