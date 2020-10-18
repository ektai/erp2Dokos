from __future__ import unicode_literals
from frappe import _

app_name = "erpnext"
app_title = "dokos"
app_publisher = "Dokos SAS"
app_description = """ERP made simple"""
app_email = "hello@dokos.io"
app_license = "GNU General Public License (v3)"
source_link = "https://gitlab.com/dokos/dokos"
app_logo_url = '/assets/erpnext/images/dokos_logo.svg'


develop_version = '1.x.x-develop'

app_include_js = "assets/js/erpnext.min.js"
app_include_css = "assets/css/erpnext.css"
web_include_js = ["assets/js/erpnext-web.min.js", "assets/js/portal-calendars.min.js"]
#web_include_css = "assets/css/erpnext-web.css"

doctype_js = {
	"Communication": "public/js/communication.js",
	"Newsletter": "public/js/newsletter.js",
	"Google Calendar": "public/js/google_calendar.js",
	"Event": "public/js/event.js"
}

welcome_email = "erpnext.setup.utils.welcome_email"

# setup wizard
setup_wizard_requires = "assets/erpnext/js/setup_wizard.js"
setup_wizard_stages = "erpnext.setup.setup_wizard.setup_wizard.get_setup_stages"
setup_wizard_test = "erpnext.setup.setup_wizard.test_setup_wizard.run_setup_wizard_test"

before_install = "erpnext.setup.install.check_setup_wizard_not_completed"
after_install = "erpnext.setup.install.after_install"

boot_session = "erpnext.startup.boot.boot_session"
notification_config = "erpnext.startup.notifications.get_notification_config"
get_help_messages = "erpnext.utilities.activation.get_help_messages"
leaderboards = "erpnext.startup.leaderboard.get_leaderboards"
filters_config = "erpnext.startup.filters.get_filters_config"

on_session_creation = [
	"erpnext.portal.utils.create_customer_or_supplier",
	"erpnext.shopping_cart.utils.set_cart_count"
]
on_logout = "erpnext.shopping_cart.utils.clear_cart_count"

treeviews = ['Account', 'Cost Center', 'Warehouse', 'Item Group', 'Customer Group', 'Sales Person', 'Territory', 'Assessment Group']

# website
update_website_context = ["erpnext.shopping_cart.utils.update_website_context"]

calendars = ["Task", "Work Order", "Leave Application", "Sales Order", "Holiday List", "Course Schedule", "Item Booking", "Event Slot", "Event Slot Booking"]
gcalendar_integrations = {
	"Item Booking": {
		"pull_insert": "erpnext.venue.doctype.item_booking.item_booking.insert_event_to_calendar",
		"pull_update": "erpnext.venue.doctype.item_booking.item_booking.update_event_in_calendar",
		"pull_delete": "erpnext.venue.doctype.item_booking.item_booking.cancel_event_in_calendar"
	}
}

domains = {
	'Distribution': 'erpnext.domains.distribution',
	'Manufacturing': 'erpnext.domains.manufacturing',
	'Retail': 'erpnext.domains.retail',
	'Services': 'erpnext.domains.services',
	'Venue': 'erpnext.domains.venue',
}

website_generators = ["Item Group", "Item", "BOM", "Sales Partner",
	"Job Opening"]

website_context = {
	"favicon": 	"/assets/erpnext/images/favicon.ico",
	"splash_image": "/assets/erpnext/images/dokos_logo.svg"
}

website_route_rules = [
	{"from_route": "/orders", "to_route": "Sales Order"},
	{"from_route": "/orders/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Sales Order",
			"parents": [{"label": _("Orders"), "route": "orders"}]
		}
	},
	{"from_route": "/invoices", "to_route": "Sales Invoice"},
	{"from_route": "/invoices/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Sales Invoice",
			"parents": [{"label": _("Invoices"), "route": "invoices"}]
		}
	},
	{"from_route": "/supplier-quotations", "to_route": "Supplier Quotation"},
	{"from_route": "/supplier-quotations/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Supplier Quotation",
			"parents": [{"label": _("Supplier Quotation"), "route": "supplier-quotations"}]
		}
	},
	{"from_route": "/purchase-orders", "to_route": "Purchase Order"},
	{"from_route": "/purchase-orders/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Purchase Order",
			"parents": [{"label": _("Purchase Order"), "route": "purchase-orders"}]
		}
	},
	{"from_route": "/purchase-invoices", "to_route": "Purchase Invoice"},
	{"from_route": "/purchase-invoices/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Purchase Invoice",
			"parents": [{"label": _("Purchase Invoice"), "route": "purchase-invoices"}]
		}
	},
	{"from_route": "/quotations", "to_route": "Quotation"},
	{"from_route": "/quotations/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Quotation",
			"parents": [{"label": _("Quotations"), "route": "quotations"}]
		}
	},
	{"from_route": "/shipments", "to_route": "Delivery Note"},
	{"from_route": "/shipments/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Delivery Note",
			"parents": [{"label": _("Shipments"), "route": "shipments"}]
		}
	},
	{"from_route": "/rfq", "to_route": "Request for Quotation"},
	{"from_route": "/rfq/<path:name>", "to_route": "rfq",
		"defaults": {
			"doctype": "Request for Quotation",
			"parents": [{"label": _("Request for Quotation"), "route": "rfq"}]
		}
	},
	{"from_route": "/addresses", "to_route": "Address"},
	{"from_route": "/addresses/<path:name>", "to_route": "addresses",
		"defaults": {
			"doctype": "Address",
			"parents": [{"label": _("Addresses"), "route": "addresses"}]
		}
	},
	{"from_route": "/jobs", "to_route": "Job Opening"},
	{"from_route": "/boms", "to_route": "BOM"},
	{"from_route": "/timesheets", "to_route": "Timesheet"},
	{"from_route": "/material-requests", "to_route": "Material Request"},
	{"from_route": "/material-requests/<path:name>", "to_route": "material_request_info",
		"defaults": {
			"doctype": "Material Request",
			"parents": [{"label": _("Material Request"), "route": "material-requests"}]
		}
	},
	{"from_route": "/bookings", "to_route": "Item Booking"}
]

standard_portal_menu_items = [
	{"title": _("Projects"), "route": "/project", "reference_doctype": "Project"},
	{"title": _("Request for Quotations"), "route": "/rfq", "reference_doctype": "Request for Quotation", "role": "Supplier"},
	{"title": _("Supplier Quotation"), "route": "/supplier-quotations", "reference_doctype": "Supplier Quotation", "role": "Supplier"},
	{"title": _("Purchase Orders"), "route": "/purchase-orders", "reference_doctype": "Purchase Order", "role": "Supplier"},
	{"title": _("Purchase Invoices"), "route": "/purchase-invoices", "reference_doctype": "Purchase Invoice", "role": "Supplier"},
	{"title": _("Quotations"), "route": "/quotations", "reference_doctype": "Quotation", "role":"Customer"},
	{"title": _("Orders"), "route": "/orders", "reference_doctype": "Sales Order", "role":"Customer"},
	{"title": _("Invoices"), "route": "/invoices", "reference_doctype": "Sales Invoice", "role":"Customer"},
	{"title": _("Shipments"), "route": "/shipments", "reference_doctype": "Delivery Note", "role":"Customer"},
	{"title": _("Issues"), "route": "/issues", "reference_doctype": "Issue", "role":"Customer"},
	{"title": _("Addresses"), "route": "/addresses", "reference_doctype": "Address"},
	{"title": _("Timesheets"), "route": "/timesheets", "reference_doctype": "Timesheet", "role":"Customer"},
	{"title": _("Newsletter"), "route": "/newsletters", "reference_doctype": "Newsletter"},
	{"title": _("Material Request"), "route": "/material-requests", "reference_doctype": "Material Request", "role": "Customer"},
	{"title": _("Bookings"), "route": "/bookings", "reference_doctype": "Item Booking", "role": "Customer"},
	{"title": _("Event Slot Bookings"), "route": "/event-slots", "reference_doctype": "Event Slot Booking", "role": "Volunteer"},
	{"title": _("Appointment Booking"), "route": "/book_appointment"},
	{"title": _("Subscription"), "route": "/subscription", "reference_doctype": "Subscription Template", "role": "Customer"}
]

default_roles = [
	{'role': 'Customer', 'doctype':'Contact', 'email_field': 'email_id'},
	{'role': 'Supplier', 'doctype':'Contact', 'email_field': 'email_id'}
]

sounds = [
	{"name": "incoming-call", "src": "/assets/erpnext/sounds/incoming-call.mp3", "volume": 0.2},
	{"name": "call-disconnect", "src": "/assets/erpnext/sounds/call-disconnect.mp3", "volume": 0.2}
]

has_website_permission = {
	"Sales Order": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Quotation": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Sales Invoice": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Supplier Quotation": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Purchase Order": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Purchase Invoice": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Material Request": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Delivery Note": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Issue": "erpnext.support.doctype.issue.issue.has_website_permission",
	"Timesheet": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Event Slot Booking": "erpnext.controllers.website_list_for_contact.has_website_permission"
}

dump_report_map = "erpnext.startup.report_data_map.data_map"

before_tests = "erpnext.setup.utils.before_tests"

standard_queries = {
	"Customer": "erpnext.selling.doctype.customer.customer.get_customer_list"
}

doc_events = {
	"Stock Entry": {
		"on_submit": "erpnext.stock.doctype.material_request.material_request.update_completed_and_requested_qty",
		"on_cancel": "erpnext.stock.doctype.material_request.material_request.update_completed_and_requested_qty"
	},
	"User": {
		"after_insert": "frappe.contacts.doctype.contact.contact.update_contact",
		"validate": "erpnext.hr.doctype.employee.employee.validate_employee_role",
		"on_update": ["erpnext.hr.doctype.employee.employee.update_user_permissions",
			"erpnext.portal.utils.set_default_role"]
	},
	("Sales Taxes and Charges Template", 'Price List'): {
		"on_update": "erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings.validate_cart_settings"
	},

	"Website Settings": {
		"validate": "erpnext.portal.doctype.products_settings.products_settings.home_page_is_products"
	},
	"Sales Invoice": {
		"on_submit": [
			"erpnext.regional.italy.utils.sales_invoice_on_submit",
			"erpnext.erpnext_integrations.taxjar_integration.create_transaction"
		],
		"on_cancel": [
			"erpnext.regional.italy.utils.sales_invoice_on_cancel",
			"erpnext.erpnext_integrations.taxjar_integration.delete_transaction"
		]
	},
	"Purchase Invoice": {
		"validate": "erpnext.regional.india.utils.update_grand_total_for_rcm"
	},
	"Payment Entry": {
		"on_submit": "erpnext.accounts.doctype.dunning.dunning.resolve_dunning"
	},
	'Address': {
		'validate': ['erpnext.regional.india.utils.validate_gstin_for_india', 'erpnext.regional.italy.utils.set_state_code', 'erpnext.regional.india.utils.update_gst_category']
	},
	('Sales Invoice', 'Sales Order', 'Delivery Note', 'Purchase Invoice', 'Purchase Order', 'Purchase Receipt'): {
		'validate': ['erpnext.regional.india.utils.set_place_of_supply']
	},
	"Contact":{
		"on_trash": "erpnext.support.doctype.issue.issue.update_issue",
		"after_insert": "erpnext.communication.doctype.call_log.call_log.set_caller_information",
		"validate": "erpnext.crm.utils.update_lead_phone_numbers"
	},
	"Lead": {
		"after_insert": "erpnext.communication.doctype.call_log.call_log.set_caller_information"
	},
	"Email Unsubscribe": {
		"after_insert": "erpnext.crm.doctype.email_campaign.email_campaign.unsubscribe_recipient"
	},
	"Quotation": {
		"on_trash": "erpnext.venue.doctype.item_booking.item_booking.delete_linked_item_bookings",
		"on_submit": "erpnext.venue.doctype.item_booking.item_booking.confirm_linked_item_bookings"
	},
	"Item Booking": {
		"after_insert": "erpnext.venue.doctype.item_booking.item_booking.insert_event_in_google_calendar",
		"on_update": "erpnext.venue.doctype.item_booking.item_booking.update_event_in_google_calendar",
		"on_cancel": "erpnext.venue.doctype.item_booking.item_booking.delete_event_in_google_calendar",
		"on_trash": "erpnext.venue.doctype.item_booking.item_booking.delete_event_in_google_calendar"
	},
	('Quotation', 'Sales Order', 'Sales Invoice'): {
		'validate': ["erpnext.erpnext_integrations.taxjar_integration.set_sales_tax"]
	}
}

# On cancel event Payment Entry will be exempted and all linked submittable doctype will get cancelled.
# to maintain data integrity we exempted payment entry. it will un-link when sales invoice get cancelled.
# if payment entry not in auto cancel exempted doctypes it will cancel payment entry.
auto_cancel_exempted_doctypes= [
	"Payment Entry",
	"Asset Movement"
]

override_doctype_dashboards = {
	"User": "erpnext.fixtures.user.get_dashboard_data",
	"Event": "erpnext.fixtures.event.get_dashboard_data",
	"Payment Gateway": "erpnext.fixtures.payment_gateway.get_dashboard_data"
}

scheduler_events = {
	"cron": {
		"0/30 * * * *": [
			"erpnext.utilities.doctype.video.video.update_youtube_data",
		]
	},
	"all": [
		"erpnext.projects.doctype.project.project.project_status_update_reminder",
		"erpnext.venue.doctype.item_booking.item_booking.clear_draft_bookings",
		"erpnext.crm.doctype.social_media_post.social_media_post.process_scheduled_social_media_posts"
	],
	"hourly": [
		'erpnext.hr.doctype.daily_work_summary_group.daily_work_summary_group.trigger_emails',
		"erpnext.accounts.doctype.subscription.subscription.process_all",
		"erpnext.erpnext_integrations.doctype.amazon_mws_settings.amazon_mws_settings.schedule_get_order_details",
		"erpnext.erpnext_integrations.doctype.plaid_settings.plaid_settings.automatic_synchronization",
		"erpnext.projects.doctype.project.project.hourly_reminder",
		"erpnext.projects.doctype.project.project.collect_project_status",
		"erpnext.hr.doctype.shift_type.shift_type.process_auto_attendance_for_all_shifts",
		"erpnext.accounts.doctype.subscription.subscription.update_grand_total"
	],
	"daily": [
		"erpnext.stock.reorder_item.reorder_item",
		"erpnext.support.doctype.issue.issue.auto_close_tickets",
		"erpnext.crm.doctype.opportunity.opportunity.auto_close_opportunity",
		"erpnext.controllers.accounts_controller.update_invoice_status",
		"erpnext.accounts.doctype.fiscal_year.fiscal_year.auto_create_fiscal_year",
		"erpnext.hr.doctype.employee.employee.send_birthday_reminders",
		"erpnext.projects.doctype.task.task.set_tasks_as_overdue",
		"erpnext.assets.doctype.asset.depreciation.post_depreciation_entries",
		"erpnext.hr.doctype.daily_work_summary_group.daily_work_summary_group.send_summary",
		"erpnext.stock.doctype.serial_no.serial_no.update_maintenance_status",
		"erpnext.buying.doctype.supplier_scorecard.supplier_scorecard.refresh_scorecards",
		"erpnext.setup.doctype.company.company.cache_companies_monthly_sales_history",
		"erpnext.assets.doctype.asset.asset.update_maintenance_status",
		"erpnext.assets.doctype.asset.asset.make_post_gl_entry",
		"erpnext.crm.doctype.contract.contract.update_status_for_contracts",
		"erpnext.projects.doctype.project.project.send_project_status_email_to_users",
		"erpnext.quality_management.doctype.quality_review.quality_review.review",
		"erpnext.support.doctype.service_level_agreement.service_level_agreement.check_agreement_status",
		"erpnext.crm.doctype.email_campaign.email_campaign.send_email_to_leads_or_contacts",
		"erpnext.crm.doctype.email_campaign.email_campaign.set_email_campaign_status",
		"erpnext.selling.doctype.quotation.quotation.set_expired_status",
		"erpnext.buying.doctype.supplier_quotation.supplier_quotation.set_expired_status",
		"erpnext.hr.doctype.holiday_list.holiday_list.replace_expired_holiday_lists",
		"erpnext.accounts.doctype.process_statement_of_accounts.process_statement_of_accounts.send_auto_email"
	],
	"daily_long": [
		"erpnext.setup.doctype.email_digest.email_digest.send",
		"erpnext.manufacturing.doctype.bom_update_tool.bom_update_tool.update_latest_price_in_all_boms",
		"erpnext.hr.doctype.leave_ledger_entry.leave_ledger_entry.process_expired_allocation",
		"erpnext.hr.utils.generate_leave_encashment",
		"erpnext.projects.doctype.project.project.update_project_sales_billing",
		"erpnext.loan_management.doctype.loan_security_shortfall.loan_security_shortfall.create_process_loan_security_shortfall",
		"erpnext.loan_management.doctype.loan_interest_accrual.loan_interest_accrual.process_loan_interest_accrual_for_term_loans",
		"erpnext.hr.utils.allocate_earned_leaves",
		"erpnext.crm.doctype.lead.lead.daily_open_lead"
	],
	"monthly_long": [
		"erpnext.accounts.deferred_revenue.process_deferred_accounting",
		"erpnext.loan_management.doctype.process_loan_interest_accrual.process_loan_interest_accrual.process_loan_interest_accrual_for_demand_loans"
	]
}

email_brand_image = "assets/erpnext/images/dokos_logo.svg"

default_mail_footer = """
	<span>
		Sent via
		<a class="text-muted" href="https://dokos.io?source=via_email_footer" target="_blank">
			dokos
		</a>
	</span>
"""

get_translated_dict = {
	("doctype", "Global Defaults"): "frappe.geo.country_info.get_translated_dict"
}

bot_parsers = [
	'erpnext.utilities.bot.FindItemBot',
]

get_site_info = 'erpnext.utilities.get_site_info'

payment_gateway_enabled = "erpnext.accounts.utils.create_payment_gateway_account"

communication_doctypes = ["Customer", "Supplier"]

regional_overrides = {
	'France': {
		'erpnext.accounts.report.balance_sheet.balance_sheet.execute': 'erpnext.regional.france.report.balance_sheet.balance_sheet.execute',
		'erpnext.hr.utils.allocate_earned_leaves': 'erpnext.regional.france.hr.utils.allocate_earned_leaves',
	},
	'India': {
		'erpnext.tests.test_regional.test_method': 'erpnext.regional.india.utils.test_method',
		'erpnext.controllers.taxes_and_totals.get_itemised_tax_breakup_header': 'erpnext.regional.india.utils.get_itemised_tax_breakup_header',
		'erpnext.controllers.taxes_and_totals.get_itemised_tax_breakup_data': 'erpnext.regional.india.utils.get_itemised_tax_breakup_data',
		'erpnext.accounts.party.get_regional_address_details': 'erpnext.regional.india.utils.get_regional_address_details',
		'erpnext.hr.utils.calculate_annual_eligible_hra_exemption': 'erpnext.regional.india.utils.calculate_annual_eligible_hra_exemption',
		'erpnext.hr.utils.calculate_hra_exemption_for_period': 'erpnext.regional.india.utils.calculate_hra_exemption_for_period',
		'erpnext.accounts.doctype.purchase_invoice.purchase_invoice.make_regional_gl_entries': 'erpnext.regional.india.utils.make_regional_gl_entries'
	},
	'United Arab Emirates': {
		'erpnext.controllers.taxes_and_totals.update_itemised_tax_data': 'erpnext.regional.united_arab_emirates.utils.update_itemised_tax_data'
	},
	'Saudi Arabia': {
		'erpnext.controllers.taxes_and_totals.update_itemised_tax_data': 'erpnext.regional.united_arab_emirates.utils.update_itemised_tax_data'
	},
	'Italy': {
		'erpnext.controllers.taxes_and_totals.update_itemised_tax_data': 'erpnext.regional.italy.utils.update_itemised_tax_data',
		'erpnext.controllers.accounts_controller.validate_regional': 'erpnext.regional.italy.utils.sales_invoice_validate',
	},
	'Germany': {
		'erpnext.controllers.accounts_controller.validate_regional': 'erpnext.regional.germany.accounts_controller.validate_regional',
	},
	'Switzerland': {
		'erpnext.accounts.page.bank_reconciliation.auto_bank_reconciliation.regional_reconciliation': 'erpnext.regional.switzerland.utils.regional_reconciliation'
	}
}
user_privacy_documents = [
	{
		'doctype': 'Lead',
		'match_field': 'email_id',
		'personal_fields': ['phone', 'mobile_no', 'fax', 'website', 'lead_name'],
	},
	{
		'doctype': 'Opportunity',
		'match_field': 'contact_email',
		'personal_fields': ['contact_mobile', 'contact_display', 'customer_name'],
	}
]

webhooks_handler = {
	"Stripe": "erpnext.erpnext_integrations.doctype.stripe_settings.stripe_settings.handle_webhooks",
	"GoCardless": "erpnext.erpnext_integrations.doctype.gocardless_settings.gocardless_settings.handle_webhooks"
}

# ERPNext doctypes for Global Search
global_search_doctypes = {
	"Default": [
		{"doctype": "Customer", "index": 0},
		{"doctype": "Supplier", "index": 1},
		{"doctype": "Item", "index": 2},
		{"doctype": "Warehouse", "index": 3},
		{"doctype": "Account", "index": 4},
		{"doctype": "Employee", "index": 5},
		{"doctype": "BOM", "index": 6},
		{"doctype": "Sales Invoice", "index": 7},
		{"doctype": "Sales Order", "index": 8},
		{"doctype": "Quotation", "index": 9},
		{"doctype": "Work Order", "index": 10},
		{"doctype": "Purchase Receipt", "index": 11},
		{"doctype": "Purchase Invoice", "index": 12},
		{"doctype": "Delivery Note", "index": 13},
		{"doctype": "Stock Entry", "index": 14},
		{"doctype": "Material Request", "index": 15},
		{"doctype": "Delivery Trip", "index": 16},
		{"doctype": "Pick List", "index": 17},
		{"doctype": "Salary Slip", "index": 18},
		{"doctype": "Leave Application", "index": 19},
		{"doctype": "Expense Claim", "index": 20},
		{"doctype": "Payment Entry", "index": 21},
		{"doctype": "Lead", "index": 22},
		{"doctype": "Opportunity", "index": 23},
		{"doctype": "Item Price", "index": 24},
		{"doctype": "Purchase Taxes and Charges Template", "index": 25},
		{"doctype": "Sales Taxes and Charges", "index": 26},
		{"doctype": "Asset", "index": 27},
		{"doctype": "Project", "index": 28},
		{"doctype": "Task", "index": 29},
		{"doctype": "Timesheet", "index": 30},
		{"doctype": "Issue", "index": 31},
		{"doctype": "Serial No", "index": 32},
		{"doctype": "Batch", "index": 33},
		{"doctype": "Branch", "index": 34},
		{"doctype": "Department", "index": 35},
		{"doctype": "Employee Grade", "index": 36},
		{"doctype": "Designation", "index": 37},
		{"doctype": "Job Opening", "index": 38},
		{"doctype": "Job Applicant", "index": 39},
		{"doctype": "Job Offer", "index": 40},
		{"doctype": "Salary Structure Assignment", "index": 41},
		{"doctype": "Appraisal", "index": 42},
		{"doctype": "Loan", "index": 43},
		{"doctype": "Maintenance Schedule", "index": 44},
		{"doctype": "Maintenance Visit", "index": 45},
		{"doctype": "Warranty Claim", "index": 46}
	]
}