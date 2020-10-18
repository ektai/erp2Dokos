// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.company");

frappe.ui.form.on("Company", {
	onload: function(frm) {
		if (frm.doc.__islocal && frm.doc.parent_company) {
			frappe.db.get_value('Company', frm.doc.parent_company, 'is_group', (r) => {
				if (!r.is_group) {
					frm.set_value('parent_company', '');
				}
			});
		}
	},
	setup: function(frm) {
		erpnext.company.setup_queries(frm);
		frm.set_query("hra_component", function(){
			return {
				filters: {"type": "Earning"}
			}
		});

		frm.set_query("parent_company", function() {
			return {
				filters: {"is_group": 1}
			}
		});

		frm.set_query("default_selling_terms", function() {
			return { filters: { selling: 1 } };
		});

 		frm.set_query("default_buying_terms", function() {
			return { filters: { buying: 1 } };
		});

		frm.set_query("default_in_transit_warehouse", function() {
			return {
				filters:{
					'warehouse_type' : 'Transit',
					'is_group': 0,
					'company': frm.doc.company
				}
			};
		});
	},

	company_name: function(frm) {
		if(frm.doc.__islocal) {
			let parts = frm.doc.company_name.split(" ");
			let abbr = $.map(parts, function (p) {
				return p? p.substr(0, 1) : null;
			}).join("");
			frm.set_value("abbr", abbr);
		}
	},

	parent_company: function(frm) {
		var bool = frm.doc.parent_company ? true : false;
		frm.set_value('create_chart_of_accounts_based_on', bool ? "Existing Company" : "");
		frm.set_value('existing_company', bool ? frm.doc.parent_company : "");
		disbale_coa_fields(frm, bool);
	},

	date_of_commencement: function(frm) {
		if(frm.doc.date_of_commencement<frm.doc.date_of_incorporation)
		{
			frappe.throw(__("Date of Commencement should be greater than Date of Incorporation"));
		}
		if(!frm.doc.date_of_commencement){
			frm.doc.date_of_incorporation = ""
		}
	},

	refresh: function(frm) {
		if(!frm.doc.__islocal) {
			frm.doc.abbr && frm.set_df_property("abbr", "read_only", 1);
			frm.set_df_property("parent_company", "read_only", 1);
			disbale_coa_fields(frm);
		}

		frm.toggle_display('address_html', !frm.doc.__islocal);
		if(!frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(frm);

			frappe.dynamic_link = {doc: frm.doc, fieldname: 'name', doctype: 'Company'}

			frm.toggle_enable("default_currency", (frm.doc.__onload &&
				!frm.doc.__onload.transactions_exist));

			frm.add_custom_button(__('Create Tax Template'), function() {
				frm.trigger("make_default_tax_template");
			});

			frm.add_custom_button(__('Cost Centers'), function() {
				frappe.set_route('Tree', 'Cost Center', {'company': frm.doc.name})
			}, __("View"));

			frm.add_custom_button(__('Chart of Accounts'), function() {
				frappe.set_route('Tree', 'Account', {'company': frm.doc.name})
			}, __("View"));

			frm.add_custom_button(__('Sales Tax Template'), function() {
				frappe.set_route('List', 'Sales Taxes and Charges Template', {'company': frm.doc.name});
			}, __("View"));

			frm.add_custom_button(__('Purchase Tax Template'), function() {
				frappe.set_route('List', 'Purchase Taxes and Charges Template', {'company': frm.doc.name});
			}, __("View"));

			frm.add_custom_button(__('Default Tax Template'), function() {
				frm.trigger("make_default_tax_template");
			}, __('Create'));
		}

		erpnext.company.set_chart_of_accounts_options(frm.doc);

	},

	make_default_tax_template: function(frm) {
		frm.call({
			method: "create_default_tax_template",
			doc: frm.doc,
			freeze: true,
			callback: function() {
				frappe.msgprint(__("Default tax templates for sales and purchase are created."));
			}
		})
	},

	onload_post_render: function(frm) {
		if(frm.get_field("delete_company_transactions").$input)
			frm.get_field("delete_company_transactions").$input.addClass("hidden");
	},

	country: function(frm) {
		erpnext.company.set_chart_of_accounts_options(frm.doc);
	},

	delete_company_transactions: function(frm) {
		frappe.verify_password(function() {
			var d = frappe.prompt({
				fieldtype:"Data",
				fieldname: "company_name",
				label: __("Please re-type company name to confirm"),
				reqd: 1,
				description: __("Please make sure you really want to delete all the transactions for this company. Your master data will remain as it is. This action cannot be undone.")
			},
			function(data) {
				if(data.company_name !== frm.doc.name) {
					frappe.msgprint(__("Company name not same"));
					return;
				}
				frappe.call({
					method: "erpnext.setup.doctype.company.delete_company_transactions.delete_company_transactions",
					args: {
						company_name: data.company_name
					},
					freeze: true,
					callback: function(r, rt) {
						if(!r.exc)
							frappe.msgprint(__("Successfully deleted all transactions related to this company!"));
					},
					onerror: function() {
						frappe.msgprint(__("Wrong Password"));
					}
				});
			},
			__("Delete all the Transactions for this Company"), __("Delete")
			);
			d.get_primary_btn().addClass("btn-danger");
		});
	}
});

// __("Standard") __("Standard with Numbers")
erpnext.company.set_chart_of_accounts_options = function(doc) {
	var selected_value = doc.chart_of_accounts;
	if(doc.country) {
		return frappe.call({
			method: "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country",
			args: {
				"country": doc.country,
				"with_standard": true
			},
			callback: function(r) {
				if(!r.exc) {
					set_field_options("chart_of_accounts", [""].concat(r.message).join("\n"));
					if(in_list(r.message, selected_value))
						cur_frm.set_value("chart_of_accounts", selected_value);
				}
			}
		})
	}
}

cur_frm.cscript.change_abbr = function() {
	var dialog = new frappe.ui.Dialog({
		title: "Replace Abbr",
		fields: [
			{"fieldtype": "Data", "label": "New Abbreviation", "fieldname": "new_abbr",
				"reqd": 1 },
			{"fieldtype": "Button", "label": "Update", "fieldname": "update"},
		]
	});

	dialog.fields_dict.update.$input.click(function() {
		var args = dialog.get_values();
		if(!args) return;
		frappe.show_alert(__("Update in progress. It might take a while."));
		return frappe.call({
			method: "erpnext.setup.doctype.company.company.enqueue_replace_abbr",
			args: {
				"company": cur_frm.doc.name,
				"old": cur_frm.doc.abbr,
				"new": args.new_abbr
			},
			callback: function(r) {
				if(r.exc) {
					frappe.msgprint(__("There were errors."));
					return;
				} else {
					cur_frm.set_value("abbr", args.new_abbr);
				}
				dialog.hide();
				cur_frm.refresh();
			},
			btn: this
		})
	});
	dialog.show();
}

erpnext.company.setup_queries = function(frm) {
	$.each([
		["default_bank_account", {"account_type": "Bank"}],
		["default_cash_account", {"account_type": "Cash"}],
		["default_receivable_account", {"account_type": "Receivable"}],
		["default_payable_account", {"account_type": "Payable"}],
		["default_expense_account", {"root_type": "Expense"}],
		["default_income_account", {"root_type": "Income"}],
		["default_payroll_payable_account", {"root_type": "Liability"}],
		["round_off_account", {"root_type": "Expense"}],
		["write_off_account", {"root_type": "Expense"}],
		["discount_allowed_account", {"root_type": "Expense"}],
		["discount_received_account", {"root_type": "Income"}],
		["exchange_gain_loss_account", {"root_type": "Expense"}],
		["unrealized_exchange_gain_loss_account", {"root_type": "Expense"}],
		["accumulated_depreciation_account",
			{"root_type": "Asset", "account_type": "Accumulated Depreciation"}],
		["depreciation_expense_account", {"root_type": "Expense", "account_type": "Depreciation"}],
		["disposal_account", {"report_type": "Profit and Loss"}],
		["default_inventory_account", {"account_type": "Stock"}],
		["cost_center", {}],
		["round_off_cost_center", {}],
		["depreciation_cost_center", {}],
		["default_employee_advance_account", {"root_type": "Asset"}],
		["expenses_included_in_asset_valuation", {"account_type": "Expenses Included In Asset Valuation"}],
		["capital_work_in_progress_account", {"account_type": "Capital Work in Progress"}],
		["asset_received_but_not_billed", {"account_type": "Asset Received But Not Billed"}]
	], function(i, v) {
		erpnext.company.set_custom_query(frm, v);
	});

	if (frm.doc.enable_perpetual_inventory) {
		$.each([
			["stock_adjustment_account",
				{"root_type": "Expense", "account_type": "Stock Adjustment"}],
			["expenses_included_in_valuation",
				{"root_type": "Expense", "account_type": "Expenses Included in Valuation"}],
			["stock_received_but_not_billed",
				{"root_type": "Liability", "account_type": "Stock Received But Not Billed"}],
			["service_received_but_not_billed",
				{"root_type": "Liability", "account_type": "Service Received But Not Billed"}],
		], function(i, v) {
			erpnext.company.set_custom_query(frm, v);
		});
	}
}

erpnext.company.set_custom_query = function(frm, v) {
	var filters = {
		"company": frm.doc.name,
		"is_group": 0
	};

	for (var key in v[1]) {
		filters[key] = v[1][key];
	}

	frm.set_query(v[0], function() {
		return {
			filters: filters
		}
	});
}

var disbale_coa_fields = function(frm, bool=true) {
	frm.set_df_property("create_chart_of_accounts_based_on", "read_only", bool);
	frm.set_df_property("chart_of_accounts", "read_only", bool);
	frm.set_df_property("existing_company", "read_only", bool);
}


frappe.tour["Company"] = [
	{
		fieldname: "abbr",
		title: __("Abbreviation"),
		description: __("Company's name abbreviation. Used to differentiate master data between several companies.")
	},
	{
		fieldname: "is_group",
		title: __("Company is a group"),
		description: __("Check this field if this company is a parent company to one or several subsidiaries created in this system.")
	},
	{
		fieldname: "default_currency",
		title: __("Company's default currency'"),
		description: __("Default currency used for this company. The accounting will be done with this currency.")
	},
	{
		fieldname: "default_letter_head",
		title: __("Company's default letter head"),
		description: __("Will be selected by default in all transactions linked with this company.")
	},
	{
		fieldname: "default_holiday_list",
		title: __("Default holiday list"),
		description: __("Holiday list used by default for this company unless specified differently at a lower level.")
	},
	{
		fieldname: "default_finance_book",
		title: __("Default Finance Book"),
		description: __("Finance book used by default for this company.")
	},
	{
		fieldname: "default_selling_terms",
		title: __("Default Selling Terms"),
		description: __("Terms and conditions used by default in sales transactions.")
	},
	{
		fieldname: "default_buying_terms",
		title: __("Default Buying Terms"),
		description: __("Terms and conditions used by default in buying transactions.")
	},
	{
		fieldname: "default_warehouse_for_sales_return",
		title: __("Default warehouse for Sales Return"),
		description: __("Default warehouse for sales return transactions.")
	},
	{
		fieldname: "country",
		title: __("Company's country"),
		description: __("Country in which this company is registered.")
	},
	{
		fieldname: "create_chart_of_accounts_based_on",
		title: __("Chart of account base"),
		description: __("Create this company's chart of account based on a standard template or an existing company's chart of account. The chart of account can be edited manually after the initial creation.")
	},
	{
		fieldname: "chart_of_accounts",
		title: __("Chart of account"),
		description: __("Template for this company's chart of account.")
	},
	{
		fieldname: "tax_id",
		title: __("Tax ID"),
		description: __("Tax ID of this company.")
	},
	{
		fieldname: "date_of_establishment",
		title: __("Date of establishment"),
		description: __("Date of establishment of this company.")
	},
	{
		fieldname: "monthly_sales_target",
		title: __("Monthly Sales Target"),
		description: __("Set a monthly sales target for this company. It will be used to create the sales chart baseline at the top of this document.")
	},
	{
		fieldname: "total_monthly_sales",
		title: __("Total Monthly Sales"),
		description: __("Total monthly sales for this company.")
	},
	{
		fieldname: "default_bank_account",
		title: __("Default Bank Account"),
		description: __("Account to use as default bank account in accounting transactions.")
	},
	{
		fieldname: "default_cash_account",
		title: __("Default Cash Account"),
		description: __("Account to use as default cash account in accounting transactions.")
	},
	{
		fieldname: "inter_banks_transfer_account",
		title: __("Inter-banks transfer account"),
		description: __("Account to use as default inter-bank transfer account in internal transfer payment entries.")
	},
	{
		fieldname: "default_receivable_account",
		title: __("Default Receivable Account"),
		description: __("Default account for receivable entries. Will be associated with auxiliary accounts.")
	},
	{
		fieldname: "round_off_account",
		title: __("Round Off Account"),
		description: __("Default account for round-offs.")
	},
	{
		fieldname: "round_off_cost_center",
		title: __("Round Off Cost Center"),
		description: __("Default cost center for round-offs.")
	},
	{
		fieldname: "write_off_account",
		title: __("Write Off Account"),
		description: __("Default account for writing off part of a transaction.")
	},
	{
		fieldname: "discount_allowed_account",
		title: __("Discount Allowed Account"),
		description: __("Default account for discounts given by the company.")
	},
	{
		fieldname: "discount_received_account",
		title: __("Discount Received Account"),
		description: __("Default account for discounts received by the company.")
	},
	{
		fieldname: "exchange_gain_loss_account",
		title: __("Exchange Gain / Loss Account"),
		description: __("Default account for exhange gain or losses.")
	},
	{
		fieldname: "unrealized_exchange_gain_loss_account",
		title: __("Unrealized Exchange Gain/Loss Account"),
		description: __("Default account for unrealized exhange gain or losses.")
	},
	{
		fieldname: "default_payable_account",
		title: __("Default Payable Account"),
		description: __("Default account for payable entries. Will be associated with auxiliary accounts.")
	},
	{
		fieldname: "default_employee_advance_account",
		title: __("Default Employee Advance Account"),
		description: __("Default account for advances to employees.")
	},
	{
		fieldname: "default_expense_account",
		title: __("Default Cost of Goods Sold Account"),
		description: __("Default account for expenses booking. Should be overriden at item group or item level.")
	},
	{
		fieldname: "default_income_account",
		title: __("Default Income Account"),
		description: __("Default account for income booking. Should be overriden at item group or item level.")
	},
	{
		fieldname: "default_deferred_revenue_account",
		title: __("Default Deferred Revenue Account"),
		description: __("Default account for deferred income booking.")
	},
	{
		fieldname: "default_deferred_expense_account",
		title: __("Default Deferred Expense Account"),
		description: __("Default account for deferred expense booking.")
	},
	{
		fieldname: "default_payroll_payable_account",
		title: __("Default Payroll Payable Account"),
		description: __("Default account for payroll payables.")
	},
	{
		fieldname: "default_expense_claim_payable_account",
		title: __("Default Expense Claim Payable Account"),
		description: __("Default account for expense claim payables.")
	},
	{
		fieldname: "cost_center",
		title: __("Default Cost Center"),
		description: __("Default cost center for this company.")
	},
	{
		fieldname: "credit_limit",
		title: __("Credit Limit"),
		description: __("Default credit limit for this company.")
	},
	{
		fieldname: "payment_terms",
		title: __("Default Payment Terms Template"),
		description: __("Default template for payment terms to use in transactions.")
	},
	{
		fieldname: "enable_perpetual_inventory",
		title: __("Enable Perpetual Inventory"),
		description: __("Enable or disable the perpetual inventory mode. In perpetual inventory, accounting entries are made for each stock ledger transaction.")
	},
	{
		fieldname: "enable_perpetual_inventory_for_non_stock_items",
		title: __("Enable Perpetual Inventory For Non Stock Items"),
		description: __("Enable or disable the perpetual inventory mode for non stock items.")
	},
	{
		fieldname: "default_inventory_account",
		title: __("Default Inventory Account"),
		description: __("Default account for stock transactions.")
	},
	{
		fieldname: "stock_adjustment_account",
		title: __("Stock Adjustment Account"),
		description: __("Default account for stock variations.")
	},
	{
		fieldname: "stock_received_but_not_billed",
		title: __("Stock Received But Not Billed"),
		description: __("Stock received but not billed account.")
	},
	{
		fieldname: "service_received_but_not_billed",
		title: __("Service Received But Not Billed"),
		description: __("Service received but not billed account.")
	},
	{
		fieldname: "expenses_included_in_valuation",
		title: __("Expenses Included In Valuation"),
		description: __("Default account for expense included in items valuation.")
	},
	{
		fieldname: "accumulated_depreciation_account",
		title: __("Accumulated Depreciation Account"),
		description: __("Default account for accumulated asset depreciation.")
	},
	{
		fieldname: "depreciation_expense_account",
		title: __("Depreciation Expense Account"),
		description: __("Account for asset depreciation expenses.")
	},
	{
		fieldname: "expenses_included_in_asset_valuation",
		title: __("Expenses Included In Asset Valuation"),
		description: __("Default account for expense included in assets valuation.")
	},
	{
		fieldname: "disposal_account",
		title: __("Gain/Loss Account on Asset Disposal"),
		description: __("Defaut account for gain / loss account on asset disposal.")
	},
	{
		fieldname: "depreciation_cost_center",
		title: __("Asset Depreciation Cost Center"),
		description: __("Default cost center for asset depreciations.")
	},
	{
		fieldname: "capital_work_in_progress_account",
		title: __("Capital Work In Progress Account"),
		description: __("Account for capital work in progress accounting.")
	},
	{
		fieldname: "asset_received_but_not_billed",
		title: __("Asset Received But Not Billed"),
		description: __("Default account for assets received but not billed.")
	},
	{
		fieldname: "exception_budget_approver_role",
		title: __("Exception Budget Approver Role"),
		description: __("Role allowing the approval of budget exceptions.")
	},
	{
		fieldname: "company_logo",
		title: __("Company Logo"),
		description: __("Add your company logo. For reference only or to be used in custom print formats.")
	},
	{
		fieldname: "date_of_incorporation",
		title: __("Date of Incorporation"),
		description: __("Date of the company's incorporation. For reference only or to be used in custom print formats.")
	},
	{
		fieldname: "date_of_commencement",
		title: __("Date of Commencement"),
		description: __("Company's date of commencement. For reference only or to be used in custom print formats.")
	},
	{
		fieldname: "phone_no",
		title: __("Phone No"),
		description: __("Company's main phone number. For reference only or to be used in custom print formats.")
	},
	{
		fieldname: "fax",
		title: __("Fax"),
		description: __("Company's main fax number. For reference only or to be used in custom print formats.")
	},
	{
		fieldname: "email",
		title: __("Email"),
		description: __("Company's main email address. For reference only or to be used in custom print formats.")
	},
	{
		fieldname: "website",
		title: __("Website"),
		description: __("Company's website. For reference only or to be used in custom print formats.")
	},
	{
		fieldname: "company_description",
		title: __("Company Description"),
		description: __("Company's description. For reference only or to be used in custom print formats.")
	},
	{
		fieldname: "registration_details",
		title: __("Registration Details"),
		description: __("Company's registration details. For reference only or to be used in custom print formats.")
	},
]
