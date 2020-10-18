<template>
	<div v-if="transactions" class="matching-box">
		<div class="text-center">
			<div class="section-title">
					<h4>{{ __("Documents") }}</h4>
			</div>
			<div>
				<div class="btn-group" role="group" aria-label="Document Options">
					<button
						v-for="(dt, i) in Object.keys(matching_documents)"
						:key="i"
						type="button"
						class="btn btn-default"
						:class="document_type==dt ? 'active': ''"
						@click="change_doctype(dt)">
							{{ __(dt)}}
					</button>
				</div>
			</div>
		</div>
		<div class="documents-table">
			<vue-good-table
				v-show="matching_documents[document_type].length"
				:columns="columns"
				:rows="rows"
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
					placeholder: __('Search for a specific document'),
				}"
				@on-selected-rows-change="onSelectedRowsChange"
			>
				<template slot="table-row" slot-scope="props">
					<span v-if="props.column.field == 'link'">
						<a :href="props.row.link" target="_blank"><i class='uil uil-external-link-alt'></i></a>
					</span>
					<span v-else-if="props.column.field == 'amount' && props.row.amount == 0">
						{{ __(props.row.status) }}
					</span>
					<span v-else>
						{{props.formattedRow[props.column.field]}}
					</span>
				</template>
			</vue-good-table>
		</div>
		<div v-show="!transactions.length && !matching_documents[document_type].length" class="flex flex-wrap justify-center align-center border rounded no-data">
			{{ __("Select a bank transaction to find matching transactions") }}
		</div>
		<div v-show="transactions.length && !matching_documents[document_type].length" class="flex flex-wrap justify-center align-center border rounded no-data">
			{{ __("No matching document found for your selection") }}
		</div>
		<div v-show="matching_documents[document_type].length || (transactions.length && !matching_documents[document_type].length)" class="text-center document-options">
			<div class="btn-group" role="group" aria-label="Document Options">
				<button type="button" class="btn btn-default" @click="get_linked_docs(false)">{{ __("Show the full list") }}</button>
				<button type="button" class="btn btn-primary" @click="create_new_document">{{ __("Create a new {0}", [__(document_type)]) }}</button>
			</div>
		</div>
	</div>
</template>

<script>
import { VueGoodTable } from 'vue-good-table';

export default {
	name: 'BankReconciliationMatchingBox',
	components: {
		VueGoodTable
	},
	props: {
		transactions: {
			type: Array,
			default: () => []
		}
	},
	data() {
		return {
			document_type: 'Payment Entry',
			matching_documents: {
				'Payment Entry': [],
				'Journal Entry': [],
				'Sales Invoice': [],
				'Purchase Invoice': [],
				'Expense Claim': []
			},
			columns: [
				{field: 'name', hidden: true},
				{label:__('Date'), field:'date', type: "date", dateInputFormat: 'yyyy-MM-dd', dateOutputFormat: frappe.datetime.get_user_date_fmt().replace(/m/g, 'M')},
				{label:__('Party'), field:'party', width: "20%"},
				{label:__('Amount'), field:'amount', type: 'decimal', formatFn: this.formatAmount, width: "30%"},
				{label:__('Reference'), field:'reference_string', width: "30%"},
				{label:__('Reference Date'), field:'reference_date', type: "date", dateInputFormat: 'yyyy-MM-dd', dateOutputFormat: frappe.datetime.get_user_date_fmt().replace(/m/g, 'M')},
				{field:'link'}
			]
		}
	},
	computed: {
		rows: function() {
			return this.matching_documents[this.document_type].map(document => ({...document,
				date: document.posting_date,
				doctype: this.document_type,
				link: `/desk#Form/${this.document_type}/${document.name}`
			}))
		}
	},
	watch: {
		transactions: function() {
			this.get_linked_docs(true)
		}
	},
	methods: {
		change_doctype: function(dt) {
			this.document_type = dt;
			this.get_linked_docs(true);
		},
		get_linked_docs: function(match) {
			frappe.xcall('erpnext.accounts.page.bank_reconciliation.bank_transaction_match.get_linked_payments',
				{bank_transactions: this.transactions, document_type: this.document_type, match: match}
			).then((result) => {
				this.matching_documents[this.document_type] = result;
			})
		},
		formatAmount(value) {
			return format_currency(value, this.transactions.length && this.transactions[0].currency)
		},
		create_new_document() {
			if (this.document_type == "Payment Entry") {
				frappe.xcall('erpnext.accounts.doctype.bank_transaction.bank_transaction.make_new_document',{
					document_type: this.document_type,
					transactions: this.transactions
				}).then(r => {
					const doclist = frappe.model.sync(r);
					frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
				})
			} else {
				frappe.new_doc(this.document_type)
			}
		},
		onSelectedRowsChange: function(params) {
			this.$emit('documentsChange', params.selectedRows)
		}
	}
}
</script>

<style lang='scss'>
@import 'node_modules/vue-good-table/dist/vue-good-table';
@import 'frappe/public/scss/good-grid.scss';

.matching-box {
	.section-title {
		border-bottom: 1px solid #d1d8dd;
		margin-bottom: 10px;
		text-transform: uppercase;
	}

	table.vgt-table {
		font-size: 1rem;
	}
}

.document-options {
	margin: 20px;
}

.no-data {
	margin: 25px;
	height: 150px;
}

.documents-table {
	margin-top: 15px;
}
</style>