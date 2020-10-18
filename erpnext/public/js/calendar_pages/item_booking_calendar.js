// Copyright (c) 2020, Dokos SAS and Contributors
// See license.txt

import { Calendar } from '@fullcalendar/core';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import dayGridPlugin from '@fullcalendar/daygrid';

erpnext.itemBookingCalendar = class ItemBookingCalendar {
	constructor(opts) {
		Object.assign(this, opts);
		this.calendar = {};
		this.wrapper = document.getElementById(this.parentId);
		this.show()
	}

	show() {
		frappe.require([
			'/assets/js/moment-bundle.min.js',
			'/assets/js/control.min.js',
			'/assets/frappe/js/frappe/utils/datetime.js'
		], () => {
			this.build_calendar()
		});
	}

	build_calendar() {
		this.calendar = new ItemCalendar(this)
	}
}

class ItemCalendar {
	constructor(parent) {
		this.parent = parent;
		this.render();
	}

	render() {
		const calendarEl = $('<div></div>').appendTo($(this.parent.wrapper));
		this.fullCalendar = new Calendar(
			calendarEl[0],
			this.calendar_options()
		)
		this.fullCalendar.render();
	}

	//TODO: Commonify
	get_initial_display_view() {
		return frappe.is_mobile() ? 'listDay' : 'timeGridWeek'
	}

	set_initial_display_view() {
		this.fullCalendar.changeView(this.get_initial_display_view());
	}

	get_header_toolbar() {
		return {
			left: frappe.is_mobile() ? 'today' : 'dayGridMonth,timeGridWeek,listDay',
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
	}

	refresh() {
		this.fullCalendar.refetchEvents();
	}

	calendar_options() {
		const me = this;
		return {
			eventClassNames: 'item-booking-calendar',
			initialView: me.get_initial_display_view(),
			headerToolbar: me.get_header_toolbar(),
			weekends: true,
			buttonText: {
				today: __("Today"),
				timeGridWeek: __("Week"),
				listDay: __("Day"),
				dayGridMonth: __("Month")
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
			noEventsContent: __("No events to display"),
			editable: false,
			events: function(info, callback) {
				return me.getBookings(info, callback)
			},
			defaultDate: this.getDefaultDate,
			eventClick: function(event) {
				me.eventClick(event)
			},
			datesSet: function(event) {
				return me.datesSet(event);
			},
			displayEventTime: this.get_time_display(),
			allDayContent: function() {
				return __("All Day");
			}
		}
	}

	getBookings(parameters, callback) {
		frappe.call("erpnext.venue.doctype.item_booking.item_booking.get_bookings_list_for_map", {
			start: moment(parameters.start).format("YYYY-MM-DD"),
			end: moment(parameters.end).format("YYYY-MM-DD")
		}).then(result => {
			this.slots = result.message || []

			callback(this.slots);
		})
	}

	eventClick(event) {
		if (frappe.datetime.get_diff(event.event.end, frappe.datetime.nowdate()) <= 0) {
			return
		}

		frappe.confirm(__('Do you want to cancel this booking ?'), () => {
			frappe.call({
				method: "erpnext.venue.doctype.item_booking.item_booking.cancel_appointment",
				args: {
					id: event.event.id
				}
			}).then(r => {
				this.refresh();
			})
		});
	}

	datesSet(event) {
		if (event.view.activeStart && this.parent.calendar_type !== "Monthly") {
			this.fullCalendar.gotoDate(event.view.activeStart)
		}
	}
}