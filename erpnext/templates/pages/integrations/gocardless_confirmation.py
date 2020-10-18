# Copyright (c) 2020, Dokos SAS and Contributors
# License: See license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.integrations.utils import get_gateway_controller

EXPECTED_KEYS = ('redirect_flow_id', 'reference_doctype', 'reference_docname')

def get_context(context):
	context.no_cache = 1

	# all these keys exist in form_dict
	if not (set(EXPECTED_KEYS) - set(frappe.form_dict.keys())):
		for key in EXPECTED_KEYS:
			context[key] = frappe.form_dict[key]

		gateway_controller = frappe.get_doc("GoCardless Settings", get_gateway_controller(context.reference_doctype, context.reference_docname))

		try:
			redirect_flow = gateway_controller.client.redirect_flows.complete(
					context.redirect_flow_id,
					params={
						"session_token": context.reference_docname
					}
				)

			payment_request = frappe.get_doc(context.reference_doctype, context.reference_docname)
			gateway_controller.handle_redirect_flow(redirect_flow, payment_request)
			frappe.local.flags.redirect_location = 'payment-success'
		except Exception as e:
			frappe.log_error(e, "GoCardless Payment Error")
			frappe.local.flags.redirect_location = 'payment-failed'
			raise frappe.Redirect

		raise frappe.Redirect

	else:
		frappe.redirect_to_message(_('Invalid link'), _('This link is not valid.<br>Please contact us.'))
		frappe.local.flags.redirect_location = frappe.local.response.location
		raise frappe.Redirect
