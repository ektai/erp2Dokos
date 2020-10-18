<template>
	<div class="flex flex-wrap justify-center">
		<div class="actions-wrapper border rounded">
			<div class="flex flex-wrap justify-center align-center">
				<div class="amount-recap">
					<h4>{{ __("Bank Transactions") }}</h4>
					<p class="strong">{{ transactions_formatted_amount }}</p>
				</div>
				<div class="amount-recap">
					<h4>{{ __("Documents") }}</h4>
					<p class="strong">{{ documents_formatted_amount }}</p>
				</div>
			</div>
			<div class="flex flex-wrap justify-center align-center">
				<a type="button" :class='(is_reconciliation_disabled || btn_clicked) ? "btn btn-success disabled" : "btn btn-success"' :disabled="is_reconciliation_disabled || btn_clicked" @click="reconcile_entries"><span>{{ btn_clicked ? __("In progress...") : __("Reconcile", null, "Bank Transaction") }}</span><i v-show="!btn_clicked" class='uil uil-check'></i></a>
			</div>
		</div>
	</div>
</template>

<script>
export default {
	name: 'BankReconciliationActions',
	props: {
		selected_transactions: {
			type: Array,
			default: () => []
		},
		selected_documents: {
			type: Array,
			default: () => []
		}
	},
	data() {
		return {
			btn_clicked: false
		}
	},
	computed: {
		transactions_formatted_amount: function() {
			return format_currency(this.transactions_amount, this.currency)
		},
		documents_formatted_amount: function() {
			return format_currency(this.documents_amount, this.currency)
		},
		transactions_amount: function() {
			return Math.abs(this.selected_transactions.reduce((p, v) => {
				return p + v.amount;
			}, 0))
		},
		documents_amount: function() {
			return Math.abs(this.selected_documents.reduce((p, v) => {
				return p + v.amount;
			}, 0))
		},
		currency: function() {
			return this.selected_transactions.length && this.selected_transactions[0].currency
		},
		is_reconciliation_disabled() {
			return this.transactions_amount == 0 || this.documents_amount == 0
		},
		is_pos() {
			return this.selected_documents.filter(f => (f.is_pos == 1 || f.is_paid == 1))
		}
	},
	methods: {
		reconcile_entries: function() {
			this.btn_clicked = true;
			if ((this.selected_transactions.length == 1 && this.selected_documents.length >= 1)
				|| (this.selected_transactions.length >= 1 && this.selected_documents.length == 1)) {
					if (["Sales Invoice", "Purchase Invoice", "Expense Claim"].includes(this.selected_documents[0]["doctype"]) && !this.is_pos.length) {
						frappe.confirm(__("This action will create a new payment entry. Do you confirm ?"), () => {
							this.call_reconciliation()
						});
					} else {
						this.call_reconciliation()
					}
			} else {
				frappe.msgprint(__("You can only reconcile one bank transaction with several documents or several bank transactions with one document."))
				this.btn_clicked = false;
			}
		},
		call_reconciliation: function() {
			frappe.xcall('erpnext.accounts.page.bank_reconciliation.bank_reconciliation.reconcile',
				{bank_transactions: this.selected_transactions, documents: !this.is_pos.length ? this.selected_documents : this.is_pos}
			).then((result) => {
				this.$emit('resetList')
				this.btn_clicked = false;
				frappe.show_alert({message: __(`${this.selected_documents.length} documents reconciled`), indicator: "green"})
			}).catch(r => {
				this.btn_clicked = false;
			})
		}
	}
	
}
</script>

<style lang='scss' scoped>
.amount-recap {
	margin: 20px;
	text-align: center;
	padding: 0 20px 0 20px;
}

.actions-wrapper {
	padding: 15px;
	width: 50%;
}

.btn-success,
.btn-success:hover {
	color: #fff;
}
</style>