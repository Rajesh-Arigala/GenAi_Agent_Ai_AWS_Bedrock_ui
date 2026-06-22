# Backend Action Lambda Features

This file summarizes the current R-Cafe backend action Lambda.

## Live Functions

- `createbooking`: Creates a reservation and writes clean data to DynamoDB.
- `getBooking`: Retrieves a reservation using Booking ID, date, and time.
- `updateBooking`: Updates name, date, time, party size, or special requests while preserving the same Booking ID.
- `deleteBooking`: Removes a confirmed reservation.
- `findBookingByName`: Uses the `r-cafe-index` GSI to find reservations by `customer_name`.

## Business Guardrails

- Maximum automatic party size is 12. Larger parties return an escalation message and are not auto-booked.
- Verified manager call/WhatsApp number: `9916437369`.
- Operating hours are 11:00 to 23:00.
- Past reservations are rejected.
- Reservations are limited to one month from current date.
- Fake names such as `User`, `John Doe`, `Guest`, `Test`, and repeated junk like `eeeee` are rejected.

## Date And Time Normalization

The backend Lambda is the final validation layer. It accepts common customer formats and normalizes before DynamoDB:

- Dates: `tomorrow`, `tomorow`, `day after`, weekdays, `27/7`, `27-7`, `27 July`, `July 27`, `27th July`, `YYYY-MM-DD`.
- Default no-year date is interpreted in fixed project year `2026`.
- No automatic rollover to 2027.
- Time: `9pm`, `9 pm`, `9.00pm`, `9:00 PM`, `21:00`, `noon`, `midnight`.
- Bare hour like `9` is rejected with an AM/PM clarification request.

## DynamoDB Fields

- `Booking_ID`
- `Booking_DateTime`
- `customer_name`
- `party_size`
- `special_requests`

## Current/Future Boundary

Current system is a single-agent booking and visit-needs assistant. Menu RAG, weather, nearby places, clothing advice, manager ticketing, missed-call verification, and automated callback are future integrations unless connected with real backend tools.

## Booking Status And Cleanup Flags

New standard bookings are written with `booking_status = active`. Customer-facing lookup and update paths should use only valid active bookings inside the one-month booking window.

Supported status values:
- `active`: current valid booking.
- `closed-executed`: booking date/time has passed.
- `invalid`: incomplete, placeholder, duplicate correction-created, or otherwise loose/wasted record.

A valid booking requires `Booking_ID`, normalized `Booking_DateTime`, first and last `customer_name`, positive `party_size`, and active status. The Lambda includes diagnostic flag logic for cleanup decisions, including missing fields, placeholder/single-part names, past bookings, outside-window bookings, invalid party sizes, and unknown statuses.

Deletion safety belongs primarily in the prompt/action flow: choosing a Booking ID after search is not enough. The agent must show the exact booking and ask for explicit cancellation confirmation before calling `deleteBooking`.
