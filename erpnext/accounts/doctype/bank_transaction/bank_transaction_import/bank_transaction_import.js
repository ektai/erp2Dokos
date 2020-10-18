import BankTransactionImporter from './BankTransactionImporter.vue';
frappe.provide("erpnext.bank_transaction")

erpnext.accounts.bankTransactionUpload = class bankTransactionUpload {
	constructor(upload_type) {
		this.data = [];
		this.upload_type = upload_type;
		erpnext.bank_transaction = {};

		frappe.utils.make_event_emitter(erpnext.bank_transaction);
		this.make();
	}

	make() {
		this.dialog = new frappe.ui.Dialog({
			size: 'large',
			title: this.upload_type == 'plaid' ? __('Synchronize an account') : __('Upload New Bank Transactions'),
			fields: [
				{
					fieldname: 'transactions',
					label: __('New Transactions'),
					fieldtype: 'HTML'
				}
			]
		})
		this.dialog.show();
		this.show_uploader();

		erpnext.bank_transaction.on('add_primary_action', () => {
			this.dialog.set_primary_action(__("Submit"), () => {
				erpnext.bank_transaction.trigger('add_bank_entries')
				this.dialog.disable_primary_action();
			})
		})

		erpnext.bank_transaction.on('add_plaid_action', () => {
			this.dialog.set_primary_action(__("Synchronize"), () => {
				erpnext.bank_transaction.trigger('synchronize_via_plaid')
				this.dialog.disable_primary_action();
			})
		})
		
		erpnext.bank_transaction.on('close_dialog', () => {
			this.dialog.hide();
			frappe.views.ListView.trigger_list_update({doctype: 'Bank Transaction'});
		})
	}

	show_uploader() {
		this.wrapper = this.dialog.fields_dict.transactions.$wrapper[0];

		frappe.xcall('erpnext.accounts.doctype.bank_transaction.bank_transaction_upload.get_bank_accounts_list')
		.then(r => {
			new Vue({
				el: this.wrapper,
				render: h => h(BankTransactionImporter, {
					props: { upload_type: this.upload_type, bank_accounts: r }
				})
			})
		})
	}
}