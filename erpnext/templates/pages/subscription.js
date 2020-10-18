frappe.ready(() => {
	frappe.require([
		'/assets/js/moment-bundle.min.js',
		'/assets/js/dialog.min.js',
		'/assets/js/control.min.js',
		'/assets/frappe/js/frappe/utils/datetime.js'
	], () => {
		new subscriptionPortal({})
	});
});

class subscriptionPortal {
	constructor(opts) {
		Object.assign(this, opts)
		this.subscription = null;
		this.subscription_plans = [];
		this.available_subscriptions = [];
		this.payment_link = null;
		this.$wrapper = document.getElementsByClassName("subscriptions-section")
		this.$current_subscription = this.$wrapper[0].getElementsByClassName("current-subscription")
		this.$available_plans = this.$wrapper[0].getElementsByClassName("available-plans")
		this.$payment_section = this.$wrapper[0].getElementsByClassName("invoicing-status")
		this.$cancellation_section = this.$wrapper[0].getElementsByClassName("cancellation-options")
		this.$available_subscriptions = this.$wrapper[0].getElementsByClassName("available-subscriptions")
		this.build()
	}

	build() {
		this.get_data()
		.then(() => {
			this.build_current_section();
			!this.subscription&&this.build_available_subscriptions()
		})
	}

	get_data() {
		return frappe.call("erpnext.templates.pages.subscription.get_subscription_context")
		.then(r => {
			if (r && r.message) {
				Object.assign(this, r.message);
			}
		})
	}

	build_current_section() {
		if (this.subscription) {
			this.build_current_subscription()
			this.build_payment_status_section()
			!this.subscription.cancellation_date&&this.build_plans()
			!this.subscription.cancellation_date&&this.build_cancellation_section()
		}
	}

	build_current_subscription() {
		this.$current_subscription[0].innerHTML = `
			<h5 class="subscriptions-section-title">${ __("Your subscription") }</h5>
			<div class="current-subscription-table"></div>
			`
		this.$current_subscription_table = document.getElementsByClassName("current-subscription-table")
		frappe.call("erpnext.templates.pages.subscription.get_subscription_table", {subscription: this.subscription.name})
		.then(r => {
			if (r && r.message) {
				this.$current_subscription_table[0].innerHTML = r.message;
				this.bind_subscription_lines()
			}
		})

		let subtitle = null;
		if (this.subscription.cancellation_date) {
			subtitle = `<h6 class="small muted">${__("This subscription will end on")} ${frappe.datetime.global_date_format(this.subscription.cancellation_date)}</h6>`
		} else if (this.next_invoice_date) {
			subtitle = `<h6 class="small muted">${__("The next invoice will be generated on")} ${frappe.datetime.global_date_format(this.next_invoice_date)}</h6>`
		}

		if (subtitle) {
			const div = document.createElement('div')
			div.classList.add('subscription-subtitle')
			div.innerHTML = subtitle
			const $title = this.$current_subscription[0].getElementsByClassName("subscriptions-section-title")[0]
			$title.parentNode.insertBefore( div, $title.nextSibling );
		}

		this.$current_subscription[0].classList.remove("hide")
	}

	bind_subscription_lines() {
		const me = this;
		this.subscription.plans.map(plan => {
			const el = document.getElementById(`${plan.name}_trash`)
			el && el.addEventListener("click", function(e) {
				return frappe.call("erpnext.templates.pages.subscription.remove_subscription_line", {subscription: me.subscription.name, line: plan.name})
				.then(r => {
					if (r && r.message) {
						me.subscription = r.message;
						me.build_current_section();
						frappe.show_alert({message: __("Line removed from your subscription"), indicator: "green"});
					}
				})
			})
		})
	}

	build_plans() {
		const plans = this.get_plans_html()
		if (plans) {
			this.$available_plans[0].innerHTML = `
				<h5 class="subscriptions-section-title">${ __("Your options") }</h5>
				<div class="card-columns">${plans}</div>`

			this.bind_plans()
			this.$available_plans[0].classList.remove("hide")
		}
	}

	get_plans_html() {
		return this.subscription_plans.map(plan => {
			const image = plan.portal_image ? `<img class="card-img-top" src="${plan.portal_image}" alt="${plan.name}">` : ''
			return `<div class="card" style="width: 18rem;">
				${image}
				<div class="card-body">
					<h5 class="card-title">${plan.name}</h5>
					<p class="card-text">${plan.portal_description || ""}</p>
					<button class="btn btn-primary" id=${frappe.scrub(plan.name)}_plan>${__("Add")}</button>
				</div>
			</div>`
		}).join("")
	}

	bind_plans() {
		const me = this;
		this.subscription_plans.map(plan => {
			document.getElementById(`${frappe.scrub(plan.name)}_plan`).addEventListener("click", function(e) {
				return frappe.call("erpnext.templates.pages.subscription.add_plan", {subscription: me.subscription.name, plan: plan.name})
				.then(r => {
					if (r && r.message) {
						me.subscription = r.message;
						me.build_current_section();
						frappe.show_alert({message: __("Plan added to your subscription"), indicator: "green"});
					}
				})
			})
		})
	}

	build_available_subscriptions() {
		const subscriptions = this.available_subscriptions.map(sub => {
			const image = sub.portal_image ? `<img class="card-img-top" src="${sub.portal_image}" alt="${sub.name}">` : ''
			return `<div class="card" style="width: 18rem;">
				${image}
				<div class="card-body">
					<h5 class="card-title">${sub.name}</h5>
					<p class="card-text">${sub.portal_description || "" }</p>
					<button class="btn btn-primary" id=${frappe.scrub(sub.name)}_subscription>${__("Subscribe")}</button>
				</div>
			</div>
			`
		}).join("")

		this.$available_subscriptions[0].innerHTML = `<div class="card-columns">${subscriptions}</div>`
		this.bind_available_subscriptions()
		this.$available_subscriptions[0].classList.remove("hide")
	}

	bind_available_subscriptions() {
		const me = this;
		this.available_subscriptions.map(sub => {
			document.getElementById(`${frappe.scrub(sub.name)}_subscription`).addEventListener("click", function(e) {
				new frappe.confirm(__('Subscribe to {0} ?', [sub.name]), function() {
					me.new_subscription(sub);
				})
			})
		})
	}

	new_subscription(sub) {
		const me = this;
		return frappe.call("erpnext.templates.pages.subscription.new_subscription", {template: sub.name})
		.then(r => {
			if (r && r.message) {
				me.subscription = r.message.subscription;
				me.payment_link = r.message.payment_link;

				frappe.show_alert({message: __("Subscription created"), indicator: "green"})
				if (me.payment_link) {
					window.location = me.payment_link;
				} else {
					me.build_current_section();
					me.remove_available_subscriptions();
				}
			}
		})
	}

	remove_available_subscriptions() {
		this.$available_subscriptions[0].classList.add("hide");
	}

	build_cancellation_section() {
		const me = this;
		this.$cancellation_section[0].innerHTML = 
			`<h5 class="subscriptions-section-title">${ __("Cancellation options") }</h5>
			<div><button class="btn btn-danger" id="subscription-cancellation-btn">${ __("Cancel my subscription") }</button></div>
			`
		document.getElementById('subscription-cancellation-btn').addEventListener("click", function(e) {
			new frappe.confirm(__('Cancel this subscription at the end of the current billing period ?'), function() {
				me.cancel_subscription();
			})
		})
		this.$cancellation_section[0].classList.remove("hide");
	}

	cancel_subscription() {
		return frappe.call("erpnext.templates.pages.subscription.cancel_subscription", {subscription: this.subscription.name})
		.then(r => {
			if (r && r.message) {
				this.subscription = r.message;
				this.build_current_section()
				this.remove_cancellation_section()
				frappe.show_alert({message: __("Subscription created"), indicator: "green"})
			}
		})
	}

	remove_cancellation_section() {
		this.$cancellation_section[0].classList.add("hide");
	}

	build_payment_status_section() {
		frappe.call("erpnext.templates.pages.subscription.get_payment_requests", {subscription: this.subscription.name})
		.then(r => {
			const status = `
				<div>
					<p>${__("Outstanding amount:")}
						<span> ${format_currency(this.subscription.outstanding_amount, this.subscription.currency)}</span>
					<p>
				</div>`

			let payment_request = "";
			if (this.subscription.outstanding_amount > 0) {
				payment_request = `<div><a class="btn btn-warning" href="${r.message[0].payment_link}">${__("Pay immediately")}</a></div>`
			} else {
				payment_request = `<div><a class="btn btn-info" href="/invoices">${ __("View invoices") }</a></div>`
			}

			this.$payment_section[0].innerHTML = 
			`<h5 class="subscriptions-section-title">${ __("Invoicing status") }</h5>
			${status}
			${payment_request}
			`
		})

		this.$payment_section[0].classList.remove("hide");
	}
}
