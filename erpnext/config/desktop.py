# coding=utf-8

from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		# Modules
		{
			"module_name": "Home",
			"category": "Modules",
			"label": _("Home"),
			"color": "#1abc9c",
			"icon": "fas fa-door-open",
			"type": "module",
			"disable_after_onboard": 1,
			"description": "Dive into the basics for your organisation's needs.",
			"onboard_present": 1
		},
		{
			"module_name": "Accounting",
			"category": "Modules",
			"label": _("Accounting"),
			"color": "#3498db",
			"icon": "fas fa-book",
			"type": "module",
			"description": "Accounts, billing, payments, cost center and budgeting."
		},
		{
			"module_name": "Selling",
			"category": "Modules",
			"label": _("Selling"),
			"color": "#1abc9c",
			"icon": "fas fa-cash-register",
			"type": "module",
			"description": "Sales orders, quotations, customers and items."
		},
		{
			"module_name": "Buying",
			"category": "Modules",
			"label": _("Buying"),
			"color": "#c0392b",
			"icon": "fas fa-shopping-bag",
			"type": "module",
			"description": "Purchasing, suppliers, material requests, and items."
		},
		{
			"module_name": "Stock",
			"category": "Modules",
			"label": _("Stock"),
			"color": "#f39c12",
			"icon": "fas fa-warehouse",
			"type": "module",
			"description": "Stock transactions, reports, serial numbers and batches."
		},
		{
			"module_name": "Assets",
			"category": "Modules",
			"label": _("Assets"),
			"color": "#4286f4",
			"icon": "fas fa-database",
			"type": "module",
			"description": "Asset movement, maintainance and tools."
		},
		{
			"module_name": "Projects",
			"category": "Modules",
			"label": _("Projects"),
			"color": "#8e44ad",
			"icon": "fas fa-project-diagram",
			"type": "module",
			"description": "Updates, Timesheets and Activities."
		},
		{
			"module_name": "CRM",
			"category": "Modules",
			"label": _("CRM"),
			"color": "#EF4DB6",
			"icon": "fas fa-funnel-dollar",
			"type": "module",
			"description": "Sales pipeline, leads, opportunities and customers."
		},
		{
			"module_name": "Loan Management",
			"category": "Modules",
			"label": _("Loan Management"),
			"color": "#EF4DB6",
			"icon": "fas fa-money-check-alt",
			"type": "module",
			"description": "Loan Management for Customer and Employees"
		},
		{
			"module_name": "Support",
			"category": "Modules",
			"label": _("Support"),
			"color": "#1abc9c",
			"icon": "fas fa-headset",
			"type": "module",
			"description": "User interactions, support issues and knowledge base."
		},
		{
			"module_name": "HR",
			"category": "Modules",
			"label": _("Human Resources"),
			"color": "#2ecc71",
			"icon": "fas fa-users",
			"type": "module",
			"description": "Employees, attendance, payroll, leaves and shifts."
		},
		{
			"module_name": "Quality Management",
			"category": "Modules",
			"label": _("Quality"),
			"color": "#1abc9c",
			"icon": "fas fa-tasks",
			"type": "module",
			"description": "Quality goals, procedures, reviews and action."
		},


		# Category: "Domains"
		{
			"module_name": "Manufacturing",
			"category": "Domains",
			"label": _("Manufacturing"),
			"color": "#7c61ff",
			"icon": "fas fa-industry",
			"type": "module",
			"description": "BOMS, work orders, operations, and timesheets."
		},
		{
			"module_name": "Retail",
			"category": "Domains",
			"label": _("Retail"),
			"color": "#61e4ff",
			"icon": "fas fa-store-alt",
			"type": "module",
			"description": "Point of Sale and cashier closing."
		},
		{
			"module_name": "Venue",
			"category": "Domains",
			"label": _("Venue"),
			"color": "#49937e",
			"icon": "fas fa-map-marked-alt",
			"type": "module",
			"description": "Venue management."
		}
	]
