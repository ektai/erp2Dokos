<template>
	<div v-show="bankAccount && start_date && end_date">
		<bank-reconciliation-chart
			:bank_account="bankAccount"
			:start_date="start_date"
			:end_date="end_date"
		/>
		<bank-reconciliation-info
			:bank_account="bankAccount"
			:start_date="start_date"
			:end_date="end_date"
		/>
		<bank-reconciliation-actions
			:selected_transactions="selectedTransactions"
			:selected_documents="selectedDocuments"
			@resetList="reset_list"
		/>
		<div class="row reconciliation-dashboard">
			<div class="col-md-6">
				<bank-reconciliation-transaction-list
					ref="transactionsList"
					:bank_account="bankAccount"
					:start_date="start_date"
					:end_date="end_date"
					:selected_transactions="selectedTransactions"
					@transactionsChange="transactions_change"
				/>
			</div>
			 <div class="col-md-6">
				<bank-reconciliation-matching-box
					:transactions="selectedTransactions"
					@documentsChange="documents_change"
				/>
			</div>
		</div>
	</div>
</template>

<script>
import BankReconciliationChart from './BankReconciliationChart.vue';
import BankReconciliationTransactionList from './BankReconciliationTransactionList.vue';
import BankReconciliationInfo from './BankReconciliationInfo.vue';
import BankReconciliationMatchingBox from './BankReconciliationMatchingBox.vue';
import BankReconciliationActions from './BankReconciliationActions.vue';

export default {
	name: 'BankReconciliation',
	components: {
		BankReconciliationChart,
		BankReconciliationTransactionList,
		BankReconciliationInfo,
		BankReconciliationMatchingBox,
		BankReconciliationActions
	},
	props: {
		bank_account: {
			type: String,
			default: null
		},
		date_range: {
			type: Array,
			default: []
		}
	},
	data() {
		return {
			bankAccount: this.bank_account,
			dateRange: this.date_range,
			selectedTransactions: [],
			selectedDocuments: []
		}
	},
	computed: {
		start_date: function() {
			return this.dateRange[0]
		},
		end_date: function() {
			return this.dateRange[1]
		}
	},
	created() {
		erpnext.bank_reconciliation.on('filter_change', data => {
			this[data.name] = data.value;
		})
	},
	methods: {
		transactions_change: function(selection) {
			this.selectedTransactions = selection;
			this.check_selected_rows()
		},
		documents_change: function(selection) {
			this.selectedDocuments = selection;
			this.check_selected_rows()
		},
		check_selected_rows: function(selection) {
			if (this.selectedTransactions.length > 1 && this.selectedDocuments.length > 1) {
				frappe.msgprint(__("Please select only one bank transaction and multiple documents or multiple bank transactions and only one document."))
			}
		},
		reset_list: function() {
			this.$refs.transactionsList.get_transaction_list(true);
		}
	}
	
}
</script>

<style lang='scss' scoped>
.reconciliation-dashboard {
	margin-top: 30px;
}

.reconciliation-btn {
	margin: 20px 0;
}
</style>