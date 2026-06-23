# R-Cafe Bedrock Action Group Functions

This is the final consolidated AWS Bedrock action-group function reference for the current prototype. Keep it in sync with:

- `lambda/bedrock_agent_lambda.py`
- `systme-prompt.md`
- DynamoDB table `Restro-Table_booking-R-Cafe`
- GSI `r-cafe-index`

## DynamoDB Fields

- `Booking_ID` - string partition key
- `Booking_DateTime` - string sort key, stored as `YYYY-MM-DD HH:MM`
- `customer_name` - string, customer first and last name, also GSI partition key
- `party_size` - number
- `booking_status` - string; expected values are `active`, `closed-executed`, or `invalid`
- `special_requests` - optional string

## IAM Permission Note

Closest-name fallback needs `dynamodb:Scan` on the table and/or `r-cafe-index` in addition to `Query`. Exact name lookup uses the `r-cafe-index` GSI. Fuzzy lookup is confirmation-gated and should return suggestions, not confirmed ownership.

## Booking Status Rules

- `active`: valid current booking in the one-month booking window.
- `closed-executed`: booking date/time has passed; historical only.
- `invalid`: loose/wasted record, correction duplicate, missing fields, placeholder/single-part customer name, internal planner text, or invalid party size.

Customer-facing lookup/update/delete flows should use only valid `active` bookings unless an administrator is explicitly doing cleanup/debugging.

## Function 1: createbooking

```json
{
  "name": "createbooking",
  "description": "Create a new R-Cafe table reservation. Backend Lambda normalizes customer-style date and time values before storing clean DynamoDB data with booking_status active.",
  "parameters": {
    "customer_name": {
      "description": "Real customer first and last name for the reservation. Do not use placeholders like User, Guest, Customer, John Doe, Test, Unknown, single names, or repeated junk text.",
      "required": "True",
      "type": "string"
    },
    "party_size": {
      "description": "Number of guests for the reservation. Standard automatic bookings support 1 to 12 guests. More than 12 requires manager approval.",
      "required": "True",
      "type": "string"
    },
    "booking_date": {
      "description": "Requested reservation date. Accept natural/customer formats such as today, tomorrow, tomorow, day after, weekdays, 27/7, 27-7, 27 July, July 27, 27th July, or YYYY-MM-DD. Backend Lambda normalizes to YYYY-MM-DD and validates the one-month booking window.",
      "required": "True",
      "type": "string"
    },
    "booking_time": {
      "description": "Requested reservation time. Accept customer formats such as 7pm, 7 pm, 7.00pm, 19:00, or 7:30 PM. Backend Lambda normalizes to 24-hour HH:MM. Bare hours like 9 require AM/PM clarification.",
      "required": "True",
      "type": "string"
    },
    "specialRequests": {
      "description": "Compact seating or accessibility notes for the reservation, such as kids, elderly guests, wheelchair access, physically disabled guests, high chair, stroller space, quiet seating, near-entrance seating, parking assistance, or drop-off assistance. Use none if the customer has no special requests.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```

## Function 2: getBooking

```json
{
  "name": "getBooking",
  "description": "Retrieve an existing active R-Cafe reservation using Booking ID plus reservation date and time.",
  "parameters": {
    "bookingId": {
      "description": "The unique booking ID, normally beginning with R-.",
      "required": "True",
      "type": "string"
    },
    "bookingDate": {
      "description": "Reservation date. Backend Lambda accepts natural/customer date formats and normalizes before lookup.",
      "required": "True",
      "type": "string"
    },
    "bookingTime": {
      "description": "Reservation time. Backend Lambda accepts customer time formats and normalizes before lookup.",
      "required": "True",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```

## Function 3: updateBooking

AWS allows a maximum of 5 parameters per function, so this function uses the compact update schema.

```json
{
  "name": "updateBooking",
  "description": "Update an existing active R-Cafe reservation. Use bookingId, bookingDate, and bookingTime to locate the reservation when known. Use updateType and newValue to describe the requested change. This compact schema stays within the AWS 5-parameter limit.",
  "parameters": {
    "bookingId": {
      "description": "The unique booking ID for the reservation being updated. If unknown, find the booking first with findBookingByName, then use the selected active booking ID.",
      "required": "False",
      "type": "string"
    },
    "bookingDate": {
      "description": "The current/original reservation date. Backend Lambda accepts natural/customer date formats and normalizes before lookup.",
      "required": "False",
      "type": "string"
    },
    "bookingTime": {
      "description": "The current/original reservation time. Backend Lambda accepts customer time formats and normalizes before lookup.",
      "required": "False",
      "type": "string"
    },
    "updateType": {
      "description": "The type of update requested. Allowed values: time, date, partySize, name, specialRequests.",
      "required": "False",
      "type": "string"
    },
    "newValue": {
      "description": "The new value for the requested update. For time use customer time or HH:MM. For date use customer date or YYYY-MM-DD. For partySize use a number. For name use the new customer first and last name. For specialRequests use compact seating/accessibility notes.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```

## Function 4: deleteBooking

```json
{
  "name": "deleteBooking",
  "description": "Delete or cancel an existing active R-Cafe reservation only after the agent has shown the exact booking and received explicit customer cancellation confirmation.",
  "parameters": {
    "bookingId": {
      "description": "The unique booking ID to delete. A Booking ID typed after search is only selection, not cancellation confirmation.",
      "required": "True",
      "type": "string"
    },
    "bookingDate": {
      "description": "Reservation date. Backend Lambda accepts natural/customer date formats and normalizes before delete.",
      "required": "True",
      "type": "string"
    },
    "bookingTime": {
      "description": "Reservation time. Backend Lambda accepts customer time formats and normalizes before delete.",
      "required": "True",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```

## Function 5: findBookingByName

```json
{
  "name": "findBookingByName",
  "description": "Find active valid R-Cafe reservations by customer name. Backend Lambda first queries exact/case-tolerant variants using the r-cafe-index GSI. If exact lookup fails, it can return closest-name suggestions from active valid bookings using first-name, last-name, and fuzzy similarity. Close matches require customer confirmation before update/delete/review.",
  "parameters": {
    "customerName": {
      "description": "Existing customer name to search. Prefer first and last name. Partial or misspelled names may return close-match suggestions that must be confirmed by the customer before taking action.",
      "required": "True",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```
