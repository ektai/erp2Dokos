# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import json
from frappe.utils import getdate, flt, formatdate
from frappe.utils.dateutils import parse_date
from six import iteritems
from ofxtools.Parser import OFXTree

@frappe.whitelist()
def upload_csv_bank_statement():
	if frappe.safe_encode(frappe.local.uploaded_filename).lower().endswith("csv".encode("utf-8")):
		from frappe.utils.csvutils import read_csv_content
		rows = read_csv_content(frappe.local.uploaded_file)

	elif frappe.safe_encode(frappe.local.uploaded_filename).lower().endswith("xlsx".encode("utf-8")):
		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
		rows = read_xlsx_file_from_attached_file(fcontent=frappe.local.uploaded_file)

	elif frappe.safe_encode(frappe.local.uploaded_filename).lower().endswith("xls".encode("utf-8")):
		from frappe.utils.xlsxutils import read_xls_file_from_attached_file
		rows = read_xls_file_from_attached_file(frappe.local.uploaded_file)

	else:
		frappe.throw(_("Please upload a csv, xls or xlsx file"))

	column_row = rows[0]
	columns = [{"field": x, "label": x} for x in column_row]
	rows.pop(0)
	data = []
	for row in rows:
		data.append(dict(zip(column_row, row)))

	return {"columns": columns, "data": data}

@frappe.whitelist()
def upload_ofx_bank_statement():
	ofx_parser = OFXTree()
	columns = [
		{
			"field": "id",
			"label": "ID",
		},
		{
			"field": "type",
			"label": _("Type")
		},
		{
			"field": "date",
			"label": _("Date"),
			"type": "date",
			"width": "100%",
			"dateInputFormat": "yyyy-MM-dd",
			"dateOutputFormat": frappe.db.get_default("date_format").replace("Y", "y").replace("m", "M").replace("D", "d") or  "yyyy-MM-dd"
		},
		{
			"field": "description",
			"label": _("Description")
		},
		{
			"field": "debit",
			"label": _("Debit"),
			"type": "decimal"
		},
		{
			"field": "credit",
			"label": _("Credit"),
			"type": "decimal"
		},
		{
			"field": "currency",
			"label": _("Currency")
		}

	]
	data = []
	try:
		from io import BytesIO
		with BytesIO(frappe.local.uploaded_file) as file:
			ofx_parser.parse(file)
			ofx = ofx_parser.convert()
			stmts = ofx.statements

			for stmt in stmts:
				txs = stmt.transactions or []
				for transaction in txs:
					data.append(make_transaction_row(transaction, stmt.curdef))
	
		return {"columns": columns, "data": data}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), _("OFX Parser Error"))
		frappe.throw(_("OFX Parser Error. Please contact the support."))

def make_transaction_row(transaction, currency=None):
	return {
		"id": transaction.fitid,
		"type": transaction.trntype,
		"date": formatdate(transaction.dtposted, "YYYY-MM-dd"),
		"description": (transaction.name or "") + " | " + (transaction.memo or ""),
		"debit": abs(transaction.trnamt) if flt(transaction.trnamt) < 0 else 0,
		"credit": transaction.trnamt if flt(transaction.trnamt) > 0 else 0,
		"currency": currency
	}

@frappe.whitelist()
def create_bank_entries(columns, data, bank_account, upload_type=None):
	if not upload_type:
		frappe.throw(_("Please upload a file first"))

	header_map = get_header_mapping(columns, bank_account, upload_type)
	if not header_map:
		return {"status": "Missing header map"}

	success = 0
	errors = 0
	duplicates = 0
	for d in json.loads(data):
		if all(item is None for item in d) is True:
			continue
		fields = {}
		for key, dummy in iteritems(header_map):
			fields.update({header_map.get(key): d.get(key)})

		try:
			bank_transaction = frappe.new_doc("Bank Transaction")
			bank_transaction.update(fields)
			bank_transaction.date = getdate(parse_date(bank_transaction.date))
			bank_transaction.bank_account = bank_account
			bank_transaction.flags.import_statement = True
			bank_transaction.insert()
			bank_transaction.submit()
			success += 1
			frappe.db.commit()
		except frappe.UniqueValidationError:
			duplicates += 1
			frappe.clear_messages()

		except frappe.DuplicateEntryError:
			duplicates += 1
			frappe.clear_messages()

		except Exception:
			errors += 1
			frappe.log_error(frappe.get_traceback(), _("Bank transaction creation error"))
			

	return {"success": success, "errors": errors, "duplicates": duplicates, "status": "Complete"}		

def get_header_mapping(columns, bank_account, upload_type):
	if upload_type == "csv":
		return get_csv_header_mapping(columns, bank_account)
	elif upload_type == "ofx":
		return get_ofx_header_mapping(columns)

def get_csv_header_mapping(columns, bank_account):
	return get_bank_mapping(bank_account)

def get_ofx_header_mapping(columns):
	return {
		"id": "reference_number",
		"date": "date",
		"description": "description",
		"debit": "debit",
		"credit": "credit"
	}

def get_bank_mapping(bank_account):
	bank_name = frappe.db.get_value("Bank Account", bank_account, "bank")
	bank = frappe.get_doc("Bank", bank_name)

	mapping = {row.file_field:row.bank_transaction_field for row in bank.bank_transaction_mapping}

	return mapping

@frappe.whitelist()
def get_bank_accounts_list():
	bank_logos = {x.get("name"): x.get("bank_logo") for x in frappe.get_all("Bank", fields=["name", "bank_logo"])}

	bank_accounts = frappe.get_all("Bank Account", filters={"is_company_account": 1}, fields=["name", "account_name", "bank", "company"])

	return [dict(x,**{"logo": bank_logos.get(x.get("bank"))}) for x in bank_accounts]
