var is_subscription = {{ is_subscription }};

const loading = (isLoading) => {
	if (isLoading) {
		document.querySelector("#card-button").disabled = true;
		document.querySelector("#loading-text").classList.remove("hidden");
		document.querySelector("#button-text").classList.add("hidden");
	} else {
		document.querySelector("#card-button").disabled = false;
		document.querySelector("#loading-text").classList.add("hidden");
		document.querySelector("#button-text").classList.remove("hidden");
	}
}

class StripeCheckout {
	constructor(opts) {
		Object.assign(this, opts)
		this.payment_key = "{{ payment_key }}";
		this.customer = "{{ customer }}";
		this.stripe = Stripe("{{ publishable_key }}", { locale: "{{ lang }}" });
		this.is_subscription = is_subscription;
		this.client_secret = null;
		this.card = null;
		this.cardButton = document.getElementById('card-button');
		this.payment_success = "{{ payment_success_redirect }}";
		this.payment_failure = "{{ payment_failure_redirect }}";

		this.is_subscription ? this.mount_card() : this.create_payment_intent();

		this.handlePaymentWithInitialPaymentMethod = this.handlePaymentWithInitialPaymentMethod.bind(this);
		this.handlePaymentRetry = this.handlePaymentRetry.bind(this);
		this.handlePaymentThatRequiresCustomerAction = this.handlePaymentThatRequiresCustomerAction.bind(this);
		this.handleRequiresPaymentMethod = this.handleRequiresPaymentMethod.bind(this);
		this.orderComplete = this.orderComplete.bind(this);
	}

	create_payment_intent() {
		frappe.call({
			method:"erpnext.templates.pages.integrations.stripe_checkout.make_payment_intent",
			args: {
				payment_key: this.payment_key,
				customer: this.customer
			}
		}).then(r => {
			this.client_secret = r.message.client_secret;
			this.mount_card();
		})
	}

	mount_card() {
		const me = this;
		this.card = this.stripe.elements().create('card', {
			hidePostalCode: true,
			style: {
				base: {
					color: '#32325d',
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
		this.card.mount('#card-element');
		this.card.on('change', function(event) {
			document.querySelector("button").disabled = event.empty;
			document.querySelector("#card-error").textContent = event.error ? event.error.message : "";
		});
	
		this.cardButton.addEventListener('click', function(ev) {
			ev.preventDefault();
			me.is_subscription ? me.checkPaymentMethod() : me.payWithCard();
		})
	}

	payWithCard() {
		const me = this;
		loading(true);
		this.stripe.confirmCardPayment(this.client_secret, {
			payment_method: {
				card: this.card
			}
		}).then(function(result) {
			if (result.error) {
				me.showCardError(result);
			} else {
				me.orderComplete(result);
			}
		});
	}

	checkPaymentMethod() {
		loading(true);
		const latestInvoicePaymentIntentStatus = localStorage.getItem('latestInvoicePaymentIntentStatus');

		if (latestInvoicePaymentIntentStatus === 'requires_payment_method') {
			const invoiceId = localStorage.getItem('latestInvoiceId');
			const isPaymentRetry = true;
			this.createPaymentMethod({
				isPaymentRetry,
				invoiceId,
			});
		} else {
			this.createPaymentMethod({});
		}
	}

	createPaymentMethod({ isPaymentRetry, invoiceId }) {
		const billingDetails = {
			name: document.querySelector('#cardholder-name').value,
			email: document.querySelector('#cardholder-email').value
		}

		this.stripe.createPaymentMethod({
			type: 'card',
			card: this.card,
			billing_details: billingDetails,
		})
		.then((result) => {
			if (result.error) {
				this.showCardError(result);
			} else {
				if (isPaymentRetry) {
					this.retryInvoiceWithNewPaymentMethod({
						customerId: this.customer,
						paymentMethodId: result.paymentMethod.id,
						invoiceId: invoiceId
					});
				} else {
					this.createSubscription({
						customerId: this.customer,
						paymentMethodId: result.paymentMethod.id
					});
				}
			}
		});
	}

	createSubscription({ customerId, paymentMethodId }) {
		return (
			frappe.call({
				method:"erpnext.templates.pages.integrations.stripe_checkout.make_subscription",
				args: {
					payment_key: this.payment_key,
					customerId: customerId,
					paymentMethodId: paymentMethodId
				}
			}).then((result) => {
				if (result.message&&result.message.error) {
					this.showCardError(result.message);
				}
				return result.message;
			}).then((result) => {
				return {
					paymentMethodId: paymentMethodId,
					subscription: result,
				};
			})
			.then(this.handlePaymentWithInitialPaymentMethod)
		);
	}

	retryInvoiceWithNewPaymentMethod({
		customerId,
		paymentMethodId,
		invoiceId,
	}) {
		return (
			frappe.call({
				method:"erpnext.templates.pages.integrations.stripe_checkout.retry_invoice",
				args: {
					payment_key: this.payment_key,
					customerId: customerId,
					paymentMethodId: paymentMethodId,
					invoiceId: invoiceId,
				}
			}).then((result) => {
				if (result.message.error) {
					this.showCardError(result.message);
				}
				return result.message;
			}).then((result) => {
				return {
					invoice: result,
					paymentMethodId: paymentMethodId,
					isRetry: true,
				};
			})
			.then(this.handlePaymentRetry)
		);
	}

	handlePaymentWithInitialPaymentMethod(data) {
		this.handlePaymentThatRequiresCustomerAction(data)
		.then(this.handleRequiresPaymentMethod)
		.then(this.orderComplete)
		.catch(error => {
			this.showCardError(error);
		})
	}

	handlePaymentRetry(data) {
		this.handlePaymentThatRequiresCustomerAction(data)
		.then(this.orderComplete)
		.catch(error => {
			this.showCardError(error);
		})
	}

	handleRequiresPaymentMethod({
		subscription,
		paymentMethodId,
	}) {
		if (subscription.status === 'active') {
			return { subscription, paymentMethodId };
		} else if (
			subscription.latest_invoice.payment_intent.status ===
			'requires_payment_method'
		) {
			localStorage.setItem('latestInvoiceId', subscription.latest_invoice.id);
			localStorage.setItem(
				'latestInvoicePaymentIntentStatus',
				subscription.latest_invoice.payment_intent.status
			);
			throw { error: { message: __('Your card was declined.') } };
		} else {
			return { subscription, paymentMethodId };
		}
	}

	handlePaymentThatRequiresCustomerAction({
		subscription,
		invoice,
		paymentMethodId,
		isRetry,
	}) {
		if (subscription && subscription.status === 'active') {
			return Promise.resolve({ subscription, paymentMethodId });
		}

		// If it's a first payment attempt, the payment intent is on the subscription latest invoice.
		// If it's a retry, the payment intent will be on the invoice itself.
		let paymentIntent = invoice ? invoice.payment_intent : subscription.latest_invoice.payment_intent;

		if (
			paymentIntent.status === 'requires_action' ||
			(isRetry === true && paymentIntent.status === 'requires_payment_method')
		) {
			return this.stripe.confirmCardPayment(paymentIntent.client_secret, {
				payment_method: paymentMethodId,
			}).then((result) => {
				if (result.error) {
					throw result;
				} else {
					if (result.paymentIntent.status === 'succeeded') {
						return {
							subscription: subscription,
							invoice: invoice,
							paymentMethodId: paymentMethodId,
						};
					}
				}
			})
		} else {
			return Promise.resolve({ subscription, priceId, paymentMethodId });
		}
	}

	orderComplete(result) {
		loading(false);

		document.querySelector(".result-message").classList.remove("hidden");
		document.querySelector("#card-button").style.display = "none";
		if (result.subscription&&result.subscription.status !== 'active') {
			setTimeout(() => {
				window.location.href = this.payment_failure;
			}, 2000);
		}

		setTimeout(() => {
			window.location.href = this.payment_success;
		}, 2000);
	}

	showCardError(event) {
		loading(false);
		var errorMsg = document.querySelector("#card-error");
		errorMsg.textContent = event.error.message;
		setTimeout(function() {
			errorMsg.textContent = "";
		}, 4000);
	}
}

new StripeCheckout();