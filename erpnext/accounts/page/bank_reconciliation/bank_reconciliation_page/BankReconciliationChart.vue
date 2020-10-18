<template>
	<div class="card my-3 chart-card">
		<frappe-charts
			v-if="showChart"
			ref="chart"
			:id="'reconciliation-chart'"
			:dataSets="data.datasets || []"
			:labels="data.labels"
			:title="title"
			:type="chartType"
			:colors="colors"
			:height="chartHeight"
			:axisOptions="axisOptions"
			:tooltipOptions="tooltipOptions"
			:lineOptions="lineOptions"
		/>
	</div>
</template>

<script>
import FrappeCharts from 'frappe/public/js/lib/FrappeCharts.vue';

export default {
	name: 'BankReconciliationChart',
	components: {
		FrappeCharts
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
		}
	},
	data() {
		return {
			showChart: false,
			data: [],
			title: null,
			chartType: 'line',
			colors: [],
			lineOptions: {},
			axisOptions: {},
			tooltipOptions: {},
			chartHeight: null
		}
	},
	mounted() {
		this.getChartData()
	},
	watch: {
		bank_account() {
			this.getChartData()
		},
		start_date() {
			this.getChartData()
		},
		end_date() {
			this.getChartData()
		}
	},
	methods: {
		getChartData: function() {
			if (this.bank_account && this.start_date && this.end_date) {
				frappe.xcall('erpnext.accounts.page.bank_reconciliation.bank_transaction_match.get_statement_chart',
					{
						account: this.bank_account,
						start_date: this.start_date,
						end_date: this.end_date
					}
				)
				.then(r => {
					if (r && !r.exc && Object.keys(r).length) {
						this.data = r.data
						this.title = r.title
						this.chartType = r.type
						this.colors = r.colors
						this.lineOptions = r.lineOptions
						this.showChart = true
					} else {
						this.showChart = false
					}
				})
			}
		}
	}
	
}
</script>

<style lang='scss' scoped>
	.chart-card {
		border: none;
	}
</style>