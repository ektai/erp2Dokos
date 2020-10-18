// Copyright (c) 2019, Dokos SAS and Contributors
// License: See license.txt

$(document).ready(function() {
	if (typeof Stripe != "undefined") {
		const stripe = Stripe("{{ publishable_key }}", { locale: "{{ lang }}" });
		frappe.require([
			'/assets/js/dialog.min.js',
			'/assets/js/control.min.js',
		], () => {
			new stripe_payment_methods({stripe: stripe});
		});
	}
});

stripe_payment_methods = class {
	constructor(opts) {
		Object.assign(this, opts);
		this.bind_buttons()
	}

	bind_buttons() {
		const me = this;
		$("#add-card").click(function(){
			me.add_new_card();
		})

		$(".remove-card").click(function(event){
			event.target.setAttribute("disabled", "disabled");
			event.target.classList.add("disabled")
			event.target.innerText = __("Processing...");
			me.delete_card(event.target.id)
		})
	}

	add_new_card() {
		$("#add-card").addClass('d-none');
		$("#card-form").addClass('d-block');
		this.cardElement = this.stripe.elements().create('card', {
			hidePostalCode: true,
			style: {
				base: {
					color: '#32325d',
					lineHeight: '18px',
					fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
					fontSmoothing: 'antialiased',
					fontSize: '16px',
					'::placeholder': {
						color: '#aab7c4'
					}
				},
				invalid: {
					color: '#fa755a',
					iconColor: '#fa755a'
				}
			}
		});
		this.cardElement.mount('#card-element');

		this.bind_card_events()
	}

	bind_card_events() {
		const me = this;
		// Handle real-time validation errors from the card Element.
		this.cardElement.addEventListener('change', function(event) {
			const displayError = document.getElementById('card-errors');
			if (event.error) {
			displayError.textContent = event.error.message;
			} else {
			displayError.textContent = '';
			}
		});
		
		// Handle form submission.
		const submitButton = document.getElementById('card-submit');
		submitButton.addEventListener('click', function(event) {
			event.preventDefault();
			event.target.disabled = true;
			event.target.classList.add("disabled")
			event.target.innerText = __("Processing...");

			me.stripe.createPaymentMethod({
				type: 'card',
				card: me.cardElement,
				billing_details: {
					name: 'Jenny Rosen',
				},
			}).then(function(result) {
				if (result.error) {
					const errorElement = document.getElementById('card-errors');
					errorElement.textContent = result.error.message;
				} else {
					me.stripeResultHandler(result);
				}
			});
		});
	}

	stripeResultHandler(result) {
		frappe.call({
			method:"erpnext.www.me.add_new_payment_card",
			freeze:true,
			headers: {"X-Requested-With": "XMLHttpRequest"},
			args: {
				payment_method: result.paymentMethod.id
			}
		}).then(r => {
			location.reload()
		});
	}

	delete_card(id) {
		frappe.confirm(
			__('Do you want to delete this payment method ?'), () => {
			frappe.call({
				method:"erpnext.www.me.remove_payment_card",
				freeze:true,
				headers: {"X-Requested-With": "XMLHttpRequest"},
				args: {
					id: id
				}
			}).then(r => {
				location.reload()
			})
		});
	}
}