<template>
	<div v-if="transactions" class="transactions-table">
		<div class="text-center">
			<div class="text-center section-title">
				<h4>{{ __("Bank Transactions") }}</h4>
			</div>
			<div>
				<div class="btn-group" role="group" aria-label="...">
					<button
						v-for="(filter, i) in [{value: 'All', label: __('All')}, {value: 'Unreconciled', label: __('Unreconciled')}, {value: 'Reconciled', label: __('Reconciled')}]"
						:key="i"
						type="button"
						class="btn btn-default"
						:class="list_filter==filter.value ? 'active': ''"
						@click="change_filter(filter)">
							{{ filter.label}}
					</button>
				</div>
			</div>
		</div>
		<div class="transactions-table">
			<vue-good-table
				v-show="transactions.length"
				:columns="columns"
				:rows="mapped_transactions"
				:fixed-header="false"
				styleClass="vgt-table striped"
				:pagination-options="{
					enabled: true,
					mode: 'records',
					perPage: 10,
					dropdownAllowAll: false,
					nextLabel: __('next'),
					prevLabel: __('prev'),
					rowsPerPageLabel: __('Rows per page'),
					ofLabel: __('of')
				}"
				:selectOptions="{
					enabled: true,
					selectOnCheckboxOnly: false,
					selectionText: __('rows selected'),
					clearSelectionText: __('clear'),
				}"
				:search-options="{
					enabled: true,
					placeholder: __('Search for a specific bank transaction'),
				}"
				:sort-options="{
					initialSortBy: {field: 'date', type: 'desc'}
				}"
				@on-selected-rows-change="onSelectedRowsChange"
			>
				<template slot="table-row" slot-scope="props">
					<span v-if="props.column.field == 'link'">
						<a :href="props.row.link" target="_blank"><i class='uil uil-external-link-alt'></i></a>
					</span>
					<span v-else>
						{{props.formattedRow[props.column.field]}}
					</span>
				</template>
			</vue-good-table>
			<div v-show="!transactions.length" class="flex flex-wrap justify-center align-center border rounded no-data">
				{{ __("No data available for this period")}}
			</div>
		</div>
		<div class="text-center document-options">
			<div class="btn-group" role="group" aria-label="Bank Transactions Options">
				<button type="button" class="btn btn-default" @click="auto_reconciliation">{{ __("Automatic reconciliation") }}</button>
				<button v-if="stripe_transactions.length" type="button" class="btn btn-default" @click="reconcile_stripe">{{ __("Reconcile Stripe Transactions") }}</button>
			</div>
		</div>
	</div>
</template>

<script>
import { VueGoodTable } from 'vue-good-table';
export default {
	name: 'BankReconciliationTransactionList',
	components: {
		VueGoodTable
	},
	props: {
		bank_account: {
			type: String,
			default: null
		},
		 start_date: {
			type: String,
			default: null
		},
		 end_date: {
			type: String,
			default: null
		},
		selected_transactions: {
			type: Array,
			default: () => []
		}
	},
	data() {
		return {
			list_filter: "Unreconciled",
			transactions: [],
			columns: [
				{field: "name", hidden: true},
				{label:__("Date"), field:"date", type: 'date', dateInputFormat: 'yyyy-MM-dd', dateOutputFormat: frappe.datetime.get_user_date_fmt().replace(/m/g, 'M')},
				{label:__("Description"), field:"description", width: "60%"},
				{label:__("Amount"), field:"amount", width: "100%", type: "decimal", formatFn: this.formatAmount},
				{field: "currency", hidden: true},
				{field: "debit", hidden: true},
				{field: "credit", hidden: true},
				{field: "allocated_amount", hidden: true},
				{field: "unallocated_amount", hidden: true},
				{field: "bank_account", hidden: true},
				{field: "reference_number", hidden: true},
				{field:'link'}
			]
		}
	},
	computed: {
		mapped_transactions() {
			return this.transactions.map(transaction => ({...transaction,
				amount: transaction.unallocated_amount,
				link: `/desk#Form/Bank Transaction/${transaction.name}`
			}))
		},
		stripe_transactions() {
			return this.transactions
				.filter(f => f.description&&f.description.toLowerCase().includes("stripe"))
				.map(transaction => ({...transaction,
					amount: transaction.credit > 0 ? transaction.unallocated_amount: -transaction.unallocated_amount
				}))
		}
	},
	mounted() {
		this.get_transaction_list(true)
	},
	watch: {
		bank_account() {
			this.get_transaction_list(true)
		},
		start_date() {
			this.get_transaction_list(true)
		},
		end_date() {
			this.get_transaction_list(true)
		}
	},
	methods: {
		get_transaction_list(init) {
			if (this.bank_account && this.start_date && this.end_date) {
				const query_filters = [
					["Bank Transaction", "bank_account", "=", this.bank_account],
					["Bank Transaction", "date", "between", [this.start_date, this.end_date]],
					["Bank Transaction", "docstatus", "=", 1]
				]

				if (this.list_filter == "Unreconciled") {
					query_filters.push(["Bank Transaction", "unallocated_amount", "!=", 0])
				} else if (this.list_filter == "Reconciled") {
					query_filters.push(["Bank Transaction", "unallocated_amount", "=", 0])
				}

				frappe.xcall('frappe.client.get_list', {
					doctype: "Bank Transaction",
					order_by: "date",
					fields: ["name", "date", "currency", "debit", "credit", "description", "allocated_amount", "unallocated_amount", "bank_account"],
					filters: query_filters,
					limit_page_length: 500,
					limit_start: init ? 0 : this.transactions.length
				}).then(r => {
					init ? this.transactions = r : this.transactions.push(r)
					if (r.length == 500) {
						this.get_transaction_list(false)
					}
				})
			}
		},
		formatAmount(value) {
			return format_currency(value, this.transactions[0].currency)
		},
		onSelectedRowsChange: function(params) {
			this.$emit('transactionsChange', params.selectedRows)
		},
		change_filter: function(filter) {
			this.list_filter = filter.value;
			this.get_transaction_list(true)
		},
		reconcile_stripe: function() {
			frappe.xcall('erpnext.accounts.page.bank_reconciliation.stripe_reconciliation.reconcile_stripe_payouts',
				{bank_transactions: this.stripe_transactions}
			).then((result) => {
				this.get_transaction_list(true)
				frappe.show_alert({message: __(`Stripe transactions reconciliation in progress`), indicator: "green"})
			})
		},
		auto_reconciliation: function() {
			frappe.xcall('erpnext.accounts.page.bank_reconciliation.auto_bank_reconciliation.auto_bank_reconciliation',
				{bank_transactions: this.mapped_transactions}
			).then((result) => {
				this.get_transaction_list(true)
				frappe.show_alert({message: __(`Automatic reconciliation in progress`), indicator: "green"})
			})
		},
	}
	
}
</script>

<style lang='scss'>
@import 'node_modules/vue-good-table/dist/vue-good-table';
@import 'frappe/public/scss/good-grid.scss';

.transactions-table {
	margin-bottom: 50px;
	.section-title {
		border-bottom: 1px solid #d1d8dd;
		margin-bottom: 10px;
		text-transform: uppercase;
	}

	table.vgt-table {
		font-size: 1rem;
	}
}

.no-data {
	margin: 25px;
	height: 150px;
}
</style>