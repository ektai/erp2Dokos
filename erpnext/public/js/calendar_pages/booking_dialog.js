// Copyright (c) 2020, Dokos SAS and Contributors
// See license.txt

import { Calendar } from '@fullcalendar/core';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import dayGridPlugin from '@fullcalendar/daygrid';

frappe.provide("erpnext.booking_dialog");
frappe.provide("erpnext.booking_dialog_update")

erpnext.booking_dialog = class BookingDialog {
	constructor(opts) {
		Object.assign(this, opts);
		this.sales_uom = null;
		this.uoms = [];
		this.uoms_btns = {};
		this.price = 0;
		this.formatted_price = '';
		this.calendar_type = "Daily"
		this.read_only = frappe.session.user === "Guest";
		this.wrapper = document.getElementById(this.parentId);
		this.show()
	}

	show() {
		frappe.require([
			'/assets/js/moment-bundle.min.js',
			'/assets/js/control.min.js',
			'/assets/frappe/js/frappe/utils/datetime.js'
		], () => {
			frappe.utils.make_event_emitter(erpnext.booking_dialog_update);
			this.get_selling_uoms()
			.then(() => {
				this.toggle_item_descriptions(false)
				this.refresh_bookings();
			})
		});
	}

	get_selling_uoms() {
		return frappe.call(
			'erpnext.venue.doctype.item_booking.item_booking.get_item_uoms',
			{ item_code: this.item }
		).then(r => {
			if (r.message) {
				this.uoms = r.message.uoms.flat()
				if (!this.uoms.includes(r.message.sales_uom) && r.message.sales_uom !== null) {
					this.uoms.unshift(r.message.sales_uom)
				}
				this.sales_uom = r.message.sales_uom
			}
		})
	}

	toggle_item_descriptions(display) {
		['item-website-description', 'item-website-specification', 'item-website-content'].forEach(el => {
			const toggledItem = document.getElementsByClassName(el)[0]
			if (toggledItem!==undefined) {
				toggledItem.style.display = display ? "flex" : "none";
			}
		})
		const calendarElem = document.getElementById('item-booking')
		if (display) {
			calendarElem.classList.remove('fade');
			this.destroy_sidebar();
			this.destroy_calendar();
		} else {
			this.build_sidebar();
			this.build_calendar();
			calendarElem.classList.add('fade');
		}
	}

	build_calendar() {
		this.calendar = new BookingCalendar(this)
	}

	destroy_calendar() {
		this.calendar.destroy();
	}

	build_sidebar() {
		this.sidebar = new BookingSidebar(this)
	}

	destroy_sidebar() {
		this.sidebar.destroy();
	}

	update_sales_uom(value) {
		this.sales_uom = value;
		this.calendar.uom = this.sales_uom
		this.calendar.get_item_calendar().then(() => {
			this.calendar.set_initial_display_view();
			this.calendar.set_option('headerToolbar', this.calendar.get_header_toolbar())
			this.calendar.set_option('displayEventTime', this.calendar.get_time_display())
			this.calendar.set_option('slotMinTime', this.calendar.start_time.toTimeString().slice(0, 8))
			this.calendar.set_option('slotMaxTime', this.calendar.end_time.toTimeString().slice(0, 8))
			this.calendar.fullCalendar&&this.calendar.fullCalendar.refetchEvents();
		})
		this.get_item_price()
	}

	get_item_price() {
		return frappe.call(
			'erpnext.venue.doctype.item_booking.item_booking.get_item_price',
			{ item_code: this.item, uom: this.sales_uom }
		).then(r => {
			if (r && r.message) {
				this.price = r.message.price ? r.message.price : 0;
				this.formatted_price = r.message.price ? r.message.price.formatted_price : __("Unavailable");
				this.sidebar.display_price();
			}
		})
	}

	refresh_bookings() {
		frappe.call("erpnext.venue.doctype.item_booking.item_booking.get_detailed_booked_slots", {
			item_code: this.item
		}).then(r => {
			this.sidebar.display_bookings(r.message);
		})
	}
}

class BookingSidebar {
	constructor(parent) {
		this.parent = parent;
		this.selector = parent.uoms.length > 1;
		this.render();
	}

	render() {
		const me = this;
		this.wrapper = $('<div class="sidebar-card sticky-top"></div>').appendTo($(this.parent.wrapper).find('.calendar-sidebar'));
		this.duration_selector_title = $(`<div class="sidebar-section"><h4>${__("Duration")}</h4></div>`).appendTo(this.wrapper);
		this.duration_selector_wrapper = $(`<div class="sidebar-durations"></div>`).appendTo(this.duration_selector_title);
		this.bookings_title = $(`<div class="sidebar-section"><h4>${__("Bookings")}</h4></div>`).appendTo(this.wrapper);
		this.bookings_display = $(`<div></div>`).appendTo(this.bookings_title);
		const fields = this.parent.uoms.map(value => {
			return {
				fieldname: value,
				label: __(value),
				fieldtype: "Check",
				onchange: function() {
					const values = me.duration_selector.get_values()
					const selection = Object.keys(values).reduce((prev, curr) => {
						return prev + parseInt(values[curr]);
					}, 0)

					if (selection >= 1) {
						me.parent.update_sales_uom(this.df.fieldname)
						me.toggle_click(this.df.fieldname)
					} else {
						this.set_value(1);
					}
				}
			}
		})

		this.duration_selector = new frappe.ui.FieldGroup({
			fields: fields,
			body: this.duration_selector_wrapper[0]
		});

		this.duration_selector.make();
		this.parent.sales_uom&&this.duration_selector.fields_dict[this.parent.sales_uom].set_value(1);
	}

	toggle_click(field) {
		this.duration_selector.fields_list.map(obj => {
			if (obj.df.fieldname !== field) {
				this.duration_selector_wrapper.find(`[data-fieldname="${obj.df.fieldname}"]`).find(`:checkbox`).prop("checked", false);
				this.duration_selector.set_value(0)
			};
		})
	}

	destroy() {
		this.wrapper.remove();
	}

	display_price() {
		if (this.price_display) {
			this.price_display[0].innerHTML = this.parent.formatted_price;
		} else {
			this.price_title = $(`<div class="sidebar-section"><h4>${__("Price")}</h4></div>`).appendTo(this.wrapper);
			this.price_display = $(`<div class="formatted-price">${this.parent.formatted_price}</div>`).appendTo(this.price_title);
		}
	}

	display_bookings(data) {
		const me = this;
		if (!data.length) {
			this.bookings_title[0].style.display = 'none';
		} else {
			this.bookings_title[0].style.display = 'block';
			const bookings = data.map(v => {
				const monthly_end = `<span class="small d-inline-block">${moment(v.ends_on).locale(frappe.boot.lang || 'en').format('Do MMMM YYYY')}</span>`
				const daily_end = `<span class="small d-inline-block">${moment(v.starts_on).locale(frappe.boot.lang || 'en').format('LT')}-${moment(v.ends_on).locale(frappe.boot.lang || 'en').format('LT')}</span>`
				return `
					<p>
						<span>${moment(v.starts_on).locale(frappe.boot.lang || 'en').format('Do MMMM YYYY')}</span>
						<span class="pull-right remove-slot" data-booking=${v.name}><i class="uil uil-trash-alt"></i></span>
						${this.parent.calendar_type === "Monthly" ? monthly_end : daily_end}
					</p>
				`
			}).join('')
			this.bookings_display[0].innerHTML = bookings;
			this.bookings_display.on('click', '.remove-slot', function(e) {
				e.preventDefault();
				const booking = $(this).attr('data-booking')
				erpnext.booking_dialog_update.trigger("remove_slot", {
					booking: booking
				})
			})
		}
	}
}

class BookingCalendar {
	constructor(parent) {
		this.parent = parent;
		this.error = null;
		this.reference = "Item Booking"
		this.slots = []
		this.alternative_items = []
		this.quotation = null
		this.loading = true
		this.uom = this.sales_uom
		this.item_calendar = []
		this.triggered = false
		erpnext.booking_dialog_update.on("remove_slot", r => {
			if (!this.triggered) {
				this.removeBookedSlot(r.booking);
				this.triggered = true;
			}
		})
		this.get_item_calendar()
		.then(() => {
			this.render();
		})
	}

	render() {
		const calendarEl = $('<div></div>').appendTo($(this.parent.wrapper).find('.calendar-card'));
		this.fullCalendar = new Calendar(
			calendarEl[0],
			this.calendar_options()
		)
		this.fullCalendar.render();
		this.alternative_items_wrapper = $('<div id="alternative-item"></div>').appendTo(calendarEl);
	}

	get_initial_display_view() {
		return this.parent.calendar_type === "Monthly" ? 'dayGridMonth' : (frappe.is_mobile() ? 'listDay' : 'timeGridWeek')
	}

	set_initial_display_view() {
		this.fullCalendar.changeView(this.get_initial_display_view());
	}

	get_header_toolbar() {
		return {
			left: this.parent.calendar_type === "Monthly" ? '' : (frappe.is_mobile() ? 'today' : 'timeGridWeek,listDay'),
			center: 'prev,title,next',
			right: frappe.is_mobile() ? 'closeButton' : 'today closeButton',
		}
	}

	get_time_display() {
		return !(this.get_initial_display_view() === "dayGridMonth")
	}

	set_option(option, value) {
		this.fullCalendar.setOption(option, value);
	}

	destroy() {
		this.fullCalendar.destroy();
		document.getElementById('alternative-item').remove();
	}

	get_item_calendar() {
		return frappe.call(
			'erpnext.venue.doctype.item_booking.item_booking.get_item_calendar',
			{ item: this.parent.item, uom: this.parent.sales_uom }
		).then(r => {
			this.parent.calendar_type = r.message.type;
			this.item_calendar = r.message.calendar;
			this.start_time = new Date(Math.min.apply(0, this.item_calendar.map(f => new Date(`2999-01-01 ${f.start_time}`))))
			this.end_time = new Date(Math.max.apply(0, this.item_calendar.map(f => new Date(`2999-01-01 ${f.end_time}`))))
		})
	}

	calendar_options() {
		const me = this;
		return {
			eventClassNames: 'booking-calendar',
			initialView: me.get_initial_display_view(),
			customButtons: {
				closeButton: {
					text: __("Close"),
					click: function() {
						me.parent.toggle_item_descriptions(true)
					}
				}
			},
			headerToolbar: me.get_header_toolbar(),
			weekends: true,
			buttonText: {
				today: __("Today"),
				timeGridWeek: __("Week"),
				listDay: __("Day")

			},
			plugins: [
				timeGridPlugin,
				listPlugin,
				interactionPlugin,
				dayGridPlugin
			],
			showNonCurrentDates: false,
			locale: frappe.boot.lang || 'en',
			timeZone: frappe.boot.timeZone || 'UTC',
			initialDate: moment().add(1,'d').format("YYYY-MM-DD"),
			noEventsContent: __("No slot available"),
			events: function(info, callback) {
				return me.getAvailableSlots(info, callback)
			},
			selectAllow: this.getSelectAllow,
			validRange: this.getValidRange,
			defaultDate: this.getDefaultDate,
			eventClick: function(event) {
				me.eventClick(event)
			},
			datesSet: function(event) {
				return me.datesSet(event);
			},
			displayEventTime: this.get_time_display(),
			slotMinTime: this.start_time.toTimeString().slice(0, 8),
			slotMaxTime: this.end_time.toTimeString().slice(0, 8),
			allDayContent: function() {
				return __("All Day");
			}
		}
	}

	getAvailableSlots(parameters, callback) {
		if (this.parent.item) {
			this.alternative_items = []
			frappe.call("erpnext.venue.doctype.item_booking.item_booking.get_availabilities", {
				start: moment(parameters.start).format("YYYY-MM-DD"),
				end: moment(parameters.end).format("YYYY-MM-DD"),
				item: this.parent.item,
				quotation: this.quotation,
				uom: this.uom,
				calendar_type: this.parent.calendar_type
			}).then(result => {
				this.slots = result.message || []

				callback(this.slots);
				this.fullCalendar.setOption('contentHeight', 'auto');
				if (!this.slots.length && this.parent.calendar_type !== "Monthly") {
					this.getAvailableItems(parameters)
				} else {
					this.removeAlternativeItems()
				}
			})
		}
	}

	getAvailableItems(parameters) {
		return frappe.call("erpnext.venue.doctype.item_booking.item_booking.get_available_item", {
			start: moment(parameters.start).format("YYYY-MM-DD"),
			end: moment(parameters.end).format("YYYY-MM-DD"),
			item: this.parent.item
		}).then(result => {
			if (result && result.message) {
				this.alternative_items = result.message;
				this.displayAlternativeItems()
			}
		})
	}

	displayAlternativeItems() {
		if (this.alternative_items.length) {
			const alternative_items_links = this.getAlernativeCards()
			this.alternative_items_wrapper[0].innerHTML = `
				<h4>${__("Alternative items")}</h4>
				${alternative_items_links}`
		}
	}

	removeAlternativeItems() {
		this.alternative_items_wrapper[0].innerHTML = "";
	}

	getAlernativeCards() {
		return this.alternative_items.map(item => {
			return `<div class="card my-1">
						<div class="row no-gutters">
							<div class="col-md-3">
								<div class="card-body">
									<a class="no-underline" href="${'/' + item.route}">
										<img class="website-image" alt=${item.item_name} src=${item.website_image || item.image || '/no-image.jpg'}>
									</a>
								</div>
							</div>
							<div class="col-md-9">
								<div class="card-body">
									<h5 class="card-title">
										<a class="text-dark" href="${'/' + item.route }">
											${item.item_name || item.name }
										</a>
									</h5>
									<p class="card-text">
										${ item.website_content || item.description || `<i class="text-muted">${ __("No description") }</i>` }
									</p>
									<a href="${'/' + item.route }" class="btn btn-sm btn-light">${ __('More details') }</a>
								</div>
							</div>
						</div>
					</div>`
		}).join('')
	}

	eventClick(event) {
		if (!this.parent.read_only) {
			this.loading = true;
			if (event.event.classNames.includes("available")) {
				this.bookNewSlot(event)
			} else {
				this.removeBookedSlot(event.event.id)
			}
		} else {
			if(localStorage) {
				localStorage.setItem("last_visited", window.location.pathname);
			}
			window.location.href = "/login"
		}
	}

	getQuotation() {
		if (!this.parent.read_only) {
			frappe.call("erpnext.shopping_cart.cart.get_cart_quotation")
			.then(r => {
				this.quotation = r.message.doc.name
			})
		}
	}

	bookNewSlot(event) {
		frappe.call("erpnext.venue.doctype.item_booking.item_booking.book_new_slot", {
			start: moment.utc(event.event.start).format("YYYY-MM-DD H:mm:SS"),
			end: moment.utc(event.event.end).format("YYYY-MM-DD H:mm:SS"),
			item: this.parent.item,
			uom: this.uom,
			user: frappe.session.user
		}).then(r => {
			this.getQuotation()
			this.updateCart(r.message.name, 1)
		})
	}

	removeBookedSlot(booking_id) {
		this.getQuotation()
		this.updateCart(booking_id, 0)
	}

	updateCart(booking, qty) {
		erpnext.shopping_cart.shopping_cart_update({
			item_code: this.parent.item,
			qty: qty,
			uom: this.uom,
			booking: booking,
			cart_dropdown: true
		}).then(() => {
			this.loading = false;
			this.fullCalendar.refetchEvents()
			this.parent.refresh_bookings()
			this.triggered = false;
		})
	}

	datesSet(event) {
		if (event.view.activeStart && this.parent.calendar_type !== "Monthly") {
			this.fullCalendar.gotoDate(event.view.activeStart)
		}
	}

	getSelectAllow(selectInfo) {
		return moment().diff(selectInfo.start) <= 0
	}

	getValidRange() {
		return { start: moment().add(1,'d').format("YYYY-MM-DD") }
	}
}