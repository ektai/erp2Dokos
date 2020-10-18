<template>
	<div class="row" style="min-height: 50vh;">
		<div v-if="error" class="col-12 text-center justify-content-center align-self-center">
			<h2>{{ error }}</h2>
		</div>
		<template v-else-if="formattedAmount">
			<div class="col-12 mb-4 text-center align-self-center">
				<h2>{{ subject }}</h2>
			</div>
			<div class="col-12 mb-2 mx-auto" :class="'col-md-' + Math.max((12/Math.max(paymentGateways.length, 2)), 3)" v-for="(gateway, index) in paymentGateways" :key="index">
				<div class="card">
					<div class="card-body text-center">
						<i :class="gateway.icon in iconMap ? iconMap[gateway.icon] : 'far fa-credit-card'"></i>
						<h5 class="card-title my-2">{{ gateway.title }}</h5>
						<button @click="getPaymentRequest(gateway.name)" class="btn btn-primary" :disabled="redirecting">
							<span v-show="redirecting">{{ __("Redirecting...") }}</span>
							<span v-show="!redirecting">{{ __("Pay") }} {{ formattedAmount }}</span>
						</button>
					</div>
				</div>
			</div>
		</template>
	</div>
</template>

<script>
const query_strings = frappe.utils.get_query_params()
export default {
	name: "PaymentSelector",
	data() {
		return {
			paymentGateways: [],
			iconMap: {
				"Credit Card": "far fa-credit-card",
				"Wire Transfer": "fas fa-exchange-alt",
				"Paypal": "fab fa-cc-paypal"
			},
			error: null,
			formattedAmount: null,
			docname: null,
			doctype: null,
			subject: null,
			redirecting: false
		}
	},
	mounted() {
		this.validateQuery()
		this.getPaymentDetails()
		this.getPaymentGateways()
	},
	methods: {
		validateQuery() {
			if (!Object.keys(query_strings).includes("link")) {
				this.error = __("Your payment link seems to be incorrect.")
				return
			}
		},
		getPaymentGateways() {
			if (this.error === null) {
				frappe.call({
					method: "erpnext.www.payments.index.get_payment_gateways",
					args: {
						link: query_strings.link
					}
				}).then(r => {
					if (r.message) {
						this.paymentGateways = r.message;
					}
				})
			}
		},
		getPaymentDetails() {
			if (this.error === null) {
				frappe.call({
					method: "erpnext.www.payments.index.get_payment_details",
					args: {
						link: query_strings.link
					}
				}).then(r => {
					if (r.message) {
						Object.keys(r.message).forEach(key => {
							this[key] = r.message[key];
						})
					}
				})
			}
		},
		getPaymentRequest(gateway) {
			this.redirecting = true;
			frappe.call({
				method: "erpnext.www.payments.index.get_payment_url",
				args: {
					link: query_strings.link,
					gateway: gateway
				}
			}).then(r => {
				if (r.message) {
					window.location.href = r.message;
				} else {
					this.error = __("An error occured")
				}
			})
		}
	}
}
</script>

<style scoped>

i {
	font-size: 4vh;
}

.card-body {
	padding: 0.75rem;
}

</style>