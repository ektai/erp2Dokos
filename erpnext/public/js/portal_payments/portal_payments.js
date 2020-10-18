import PaymentSelector from './PaymentSelector.vue';

frappe.ready(() => {
	new Vue({
		el: '#mainview',
		render: h => h(PaymentSelector)
	})
})