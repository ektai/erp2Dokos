// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.provide("erpnext.integrations");

frappe.ui.form.on('Plaid Settings', {
	enabled: function (frm) {
		frm.toggle_reqd('plaid_client_id', frm.doc.enabled);
		frm.toggle_reqd('plaid_secret', frm.doc.enabled);
		frm.toggle_reqd('plaid_public_key', frm.doc.enabled);
		frm.toggle_reqd('plaid_env', frm.doc.enabled);
	},
	refresh: function (frm) {
		if (frm.doc.enabled) {
			frm.add_custom_button('Link a new bank account', () => {
				new erpnext.integrations.plaidLink(frm);
			});
		}
	}
});

erpnext.integrations.plaidLink = class plaidLink {
	constructor(parent) {
		this.frm = parent;
		this.plaidUrl = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js';
		this.init_config();
	}

	async init_config() {
		this.product = ["auth", "transactions"];
		this.plaid_env = this.frm.doc.plaid_env;
		this.client_name = frappe.boot.sitename;
		this.token = await this.frm.call("get_link_token").then(resp => resp.message);
		this.init_plaid();
	}

	init_plaid() {
		const me = this;
		me.loadScript(me.plaidUrl)
			.then(() => {
				me.onScriptLoaded(me);
			})
			.then(() => {
				if (me.linkHandler) {
					me.linkHandler.open();
				}
			})
			.catch((error) => {
				me.onScriptError(error);
			});
	}

	loadScript(src) {
		return new Promise(function (resolve, reject) {
			if (document.querySelector('script[src="' + src + '"]')) {
				resolve();
				return;
			}
			const el = document.createElement('script');
			el.type = 'text/javascript';
			el.async = true;
			el.src = src;
			el.addEventListener('load', resolve);
			el.addEventListener('error', reject);
			el.addEventListener('abort', reject);
			document.head.appendChild(el);
		});
	}

	onScriptLoaded(me) {
		const lang = ['fr', 'es'].includes(frappe.boot.lang) ? frappe.boot.lang : 'en'
		me.linkHandler = Plaid.create({
			clientName: me.client_name,
			product: me.product,
			env: me.plaid_env,
			token: me.token,
			onSuccess: me.plaid_success,
			language: lang,
			countryCodes: ['CA', 'FR', 'IE', 'ES', 'GB', 'US']
		});
	}

	onScriptError(error) {
		frappe.msgprint("There was an issue connecting to Plaid's authentication server");
		frappe.msgprint(error);
	}

	plaid_success(token, response) {
		const me = this;

		frappe.prompt({
			fieldtype: "Link",
			options: "Company",
			label: __("Company"),
			fieldname: "company",
			reqd: 1
		}, (data) => {
			me.company = data.company;
			frappe.xcall('erpnext.erpnext_integrations.doctype.plaid_settings.plaid_settings.add_institution', {
				token: token,
				response: response
			}).then((result) => {
				frappe.xcall('erpnext.erpnext_integrations.doctype.plaid_settings.plaid_settings.add_bank_accounts', {
					response: response,
					bank: result,
					company: me.company
				});
			}).then(() => {
				frappe.show_alert({ message: __("Bank accounts added"), indicator: 'green' });
			});
		}, __("Select a company"), __("Continue"));
	}
};
