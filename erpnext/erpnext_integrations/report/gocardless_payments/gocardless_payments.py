# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from pandas import pandas as pd
from erpnext.erpnext_integrations.doctype.gocardless_settings.api import GoCardlessPayments

def execute(filters=None):
	columns = get_columns(filters)
	data, chart = get_data(filters)
	return columns, data, [], chart

def get_data(filters):
	gocardless_payments = get_gocardless_payments(filters)

	for payment in gocardless_payments:
		references = frappe.get_all("Integration Request", filters={"service_id": payment.get("payment_id"), "integration_request_service": "GoCardless"}, fields=["name", "reference_doctype", "reference_docname"])
		payments = [x.reference_docname for x in references if x.reference_doctype == "Payment Entry"] + [x.name for x in frappe.get_all("Payment Entry", filters={"reference_no": payment.get("payment_id"), "docstatus": 1})]
		subscriptions = [x.subscription for x in frappe.get_all("Payment Entry", filters={"name": ("in", list(set(payments)))}, fields=["subscription"])]
		payment["dokos_payments"] = " ,".join(list(set(payments))) if payments else ""
		payment["dokos_payment_status"] = " ,".join([_(x.status, context="Payment Entry") for x in frappe.get_all("Payment Entry", filters={"name": ("in", payments)}, fields=["status"])])
		payment["dokos_subscription"] = " ,".join(list(set(subscriptions))) if subscriptions and subscriptions[0] is not None else ""

	if filters.get("subscription"):
		gocardless_payments = [x for x in gocardless_payments if filters.get("subscription") in x.get("dokos_subscription")]

	return gocardless_payments, get_chart(filters, gocardless_payments)

def get_gocardless_payments(filters):
	query_filters={"gateway_settings": "GoCardless Settings"}
	if filters.get("payment_gateway"):
		query_filters.update({"name": filters.get("payment_gateway")})

	gocardless_gateways = frappe.get_all("Payment Gateway", filters=query_filters, fields=["gateway_controller"])

	params = {}
	if filters.get("date_range"):
		params = {
			"charge_date[gte]": filters.get("date_range")[0],
			"charge_date[lte]": filters.get("date_range")[1]
		}

	payments = []
	for gateway in gocardless_gateways:
		settings = frappe.get_doc("GoCardless Settings", gateway.gateway_controller)
		payments.extend(GoCardlessPayments(settings).get_list(params).records)

	output = []
	for payment in payments:
		output.append(
			{
				"payment_id": payment.attributes.get("id"),
				"charge_date": payment.attributes.get("charge_date"),
				"amount": flt(payment.attributes.get("amount")) / 100,
				"description": payment.attributes.get("description"),
				"currency": payment.attributes.get("currency"),
				"gocardless_status": _(frappe.unscrub(payment.attributes.get("status"))),
				"reference": payment.attributes.get("reference")
			}
		)

	return output

def get_columns(filters):
	return [
		{
			"fieldname": "payment_id",
			"fieldtype": "Data",
			"label": _("GoCardless Payment ID"),
			"width": 200
		},
		{
			"fieldname": "charge_date",
			"fieldtype": "Date",
			"label": _("Charge Date"),
			"width": 100
		},
		{
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": _("Amount"),
			"width": 150
		},
		{
			"fieldname": "description",
			"fieldtype": "Small Text",
			"label": _("Description"),
			"width": 250
		},
		{
			"fieldname": "gocardless_status",
			"fieldtype": "Data",
			"label": _("GoCardless Status"),
			"width": 150
		},
		{
			"fieldname": "dokos_payments",
			"fieldtype": "Data",
			"label": _("Dokos Payment"),
			"options": "Payment Entry",
			"width": 150
		},
		{
			"fieldname": "dokos_payment_status",
			"fieldtype": "Data",
			"label": _("Dokos Payment Status"),
			"width": 150
		},
		{
			"fieldname": "dokos_subscription",
			"fieldtype": "Data",
			"label": _("Subscription"),
			"options": "Subscription",
			"width": 250
		}
	]

def get_chart(filters, data):
	result = []
	df = pd.DataFrame.from_records(data)
	if not df.empty:
		df['date'] = pd.to_datetime(df['charge_date'])
		aggregate = df.groupby([df['date'].dt.strftime('%Y'), df['date'].dt.strftime('%B')])['amount'].sum().sort_values()

		result = aggregate.to_dict()

	return {
		"data" : {
			"labels" : ["{0} {1}".format(_(x[1]), x[0]) for x in result],
			"datasets" : [
				{
					"name" : _("Amount"),
					"values" : [result[x] for x in result]
				}
			]
		},
		"type" : "line",
		"colors": ['rgb(3, 37, 80)']
	}