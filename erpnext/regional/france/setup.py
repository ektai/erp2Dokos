# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
import os
from frappe.utils import cint
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup(company=None, patch=True):
	setup_company_independent_fixtures()
	setup_default_leaves()
	if not patch:
		make_fixtures(company)

def setup_company_independent_fixtures():
	make_custom_fields()
	add_custom_roles_for_reports()

def make_custom_fields():
	custom_fields = {
		'Company': [
			dict(fieldname='siren_number', label='SIREN Number',
			fieldtype='Data', insert_after='website')
		],
		'Account': [
			dict(fieldname='negative_in_balance_sheet', label='Negative in Balance Sheet',
			fieldtype='Check', insert_after='include_in_gross', depends_on='eval:doc.report_type=="Balance Sheet" && !doc.is_group',
			description='Balance is debit for asset or credit for liability accounts'),
			dict(fieldname='balance_sheet_alternative_category', label='Balance Sheet Other Category',
			fieldtype='Link', options='Account', insert_after='parent_account', depends_on='eval:doc.report_type=="Balance Sheet" && !doc.is_group')
		]
	}

	create_custom_fields(custom_fields, ignore_validate=True)

def add_custom_roles_for_reports():
	report_name = 'Fichier des Ecritures Comptables [FEC]'

	if not frappe.db.get_value('Custom Role', dict(report=report_name)):
		frappe.get_doc(dict(
			doctype='Custom Role',
			report=report_name,
			roles= [
				dict(role='Accounts Manager')
			]
		)).insert()

def make_fixtures(company=None):
	company = company.name if company else frappe.db.get_value("Global Defaults", None, "default_company")
	company_doc = frappe.get_doc("Company", company)

	if company_doc.chart_of_accounts == "Plan Comptable Général":
		accounts = frappe.get_all("Account", filters={"disabled": 0, "is_group": 0, "company": company}, fields=["name", "account_number"])
		account_map = default_accounts_mapping(accounts, company_doc)
		for account in account_map:
			frappe.db.set_value("Company", company, account, account_map[account])


def default_accounts_mapping(accounts, company):
	account_map = {
		"inter_banks_transfer_account": 580,
		"default_receivable_account": 411,
		"round_off_account": 658,
		"write_off_account": 658,
		"discount_allowed_account": 709,
		"discount_received_account": 609,
		"exchange_gain_loss_account": 666,
		"unrealized_exchange_gain_loss_account": 686,
		"default_payable_account": 401,
		"default_employee_advance_account": 425,
		"default_expense_account": 600,
		"default_income_account": 706 if company.domain == "Services" else 701,
		"default_deferred_revenue_account": 487,
		"default_deferred_expense_account": 486,
		"default_payroll_payable_account": 421,
		"default_expense_claim_payable_account": 421,
		"default_inventory_account": 310,
		"stock_adjustment_account": 603,
		"stock_received_but_not_billed": 4081,
		"service_received_but_not_billed": 4081,
		"expenses_included_in_valuation": 608,
		"accumulated_depreciation_account": 281,
		"depreciation_expense_account": 681,
		"expenses_included_in_asset_valuation": 608,
		"disposal_account": 675,
		"capital_work_in_progress_account": 231,
		"asset_received_but_not_billed": 722,
		"default_down_payment_receivable_account": 4191,
		"default_down_payment_payable_account": 4091
	}

	return {x: ([y.name for y in accounts if cint(y.account_number)==account_map[x]] or [""])[0] for x in account_map}

def setup_default_leaves():
	leave_types = frappe.get_all("Leave Type")
	for leave_type in leave_types:
		frappe.delete_doc("Leave Type", leave_type.name)

	leave_types = [
		{'doctype': 'Leave Type', 'leave_type_name': _('Casual Leave'), 'name': _('Casual Leave'),
			'allow_encashment': 0, 'is_carry_forward': 0, 'include_holiday': 1},
		{'doctype': 'Leave Type', 'leave_type_name': _('Compensatory Off'), 'name': _('Compensatory Off'),
			'allow_encashment': 0, 'is_carry_forward': 0, 'include_holiday': 1, 'is_compensatory':0, 'max_leaves_allowed': 10 },
		{'doctype': 'Leave Type', 'leave_type_name': _('Privilege Leave'), 'name': _('Privilege Leave'),
			'allow_encashment': 0, 'is_carry_forward': 0, 'include_holiday': 1, 'is_compensatory':0,
			'max_leaves_allowed': 25, 'allow_negative': 1, 'is_earned_leave': 1, 'earned_leave_frequency': 'Custom Formula',
			'earned_leave_frequency_formula': 'Congés payés sur jours ouvrables'}
	]

	for leave_type in leave_types:
		try:
			doc = frappe.get_doc(leave_type)
			doc.insert(ignore_permissions=True)
		except frappe.DuplicateEntryError:
			pass

	policy = {
		"doctype": "Leave Policy",
		"policy_title": _("Example"),
		"leave_policy_details": [
			{
				"leave_type": _('Privilege Leave'),
				"annual_allocation": 25
			},
			{
				"leave_type": _('Compensatory Off'),
				"annual_allocation": 10
			}
		]
	}

	try:
		doc = frappe.get_doc(policy)
		doc.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		pass
