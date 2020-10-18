// Copyright (c) 2020, Dokos SAS and Contributors
// See license.txt

import { Calendar } from '@fullcalendar/core';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';
import dayGridPlugin from '@fullcalendar/daygrid';

erpnext.eventSlotsBookings = class EventSlotsBookings {
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
		this.calendar = new EventsCalendar(this)
	}
}

class EventsCalendar {
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
			eventClassNames: 'event-slot-calendar',
			initialView: me.get_initial_display_view(),
			headerToolbar: me.get_header_toolbar(),
			weekends: true,
			allDayContent: function() {
				return __("All Day");
			},
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
			events: function(info, callback) {
				return me.getAvailableSlots(info, callback)
			},
			eventContent: function(info) {
				return { html: `${info.event.extendedProps.description}`};
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
			height: "auto"
		}
	}

	getAvailableSlots(parameters, callback) {
		frappe.call("erpnext.venue.doctype.event_slot.event_slot.get_available_slots", {
			start: moment(parameters.start).format("YYYY-MM-DD"),
			end: moment(parameters.end).format("YYYY-MM-DD")
		}).then(result => {
			this.slots = result.message || []

			callback(this.slots);
		})
	}

	eventClick(event) {
		const me = this;
		const dialog = new frappe.ui.Dialog ({
			size: 'large',
			title: __(event.event.title),
			fields: [
				{
					"fieldtype": "HTML",
					"fieldname": "event_description"
				}
			],
			primary_action_label: __("Register"),
			primary_action() {
				frappe.confirm(__('Do you want to register yourself for this slot ?'), () => {
					frappe.call("erpnext.venue.doctype.event_slot_booking.event_slot_booking.register_for_slot", {
						slot: event.event.id
					})
					.then(() => {
						dialog.hide()
						me.refresh();
					})
				});
			}
		});
		const description = event.event.extendedProps.content ? event.event.extendedProps.content : `<div>${__("No description")}</div>`
		dialog.fields_dict.event_description.$wrapper.html(description);
		$(dialog.footer).prepend(`
			<span class="mr-2">
				${event.event.extendedProps.booked_by_user ? __("You are already registered") + "<br/>" : ""}
				${(event.event.extendedProps.available_slots - event.event.extendedProps.booked_slots) + " " + __("slots available")}
			</span>`
		)

		if (event.event.extendedProps.booked_slots >= event.event.extendedProps.available_slots || event.event.extendedProps.booked_by_user) {
			dialog.disable_primary_action();
		}
		dialog.show()
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