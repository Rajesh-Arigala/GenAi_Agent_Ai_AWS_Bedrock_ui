# R-Cafe Bedrock Action Group Functions

This file is the AWS Bedrock action-group function reference. It must stay in sync with:

- `lambda/bedrock_agent_lambda.py`
- `systme-prompt.md`
- DynamoDB table `Restro-Table_booking-R-Cafe`
- GSI `r-cafe-index`

## DynamoDB Fields

- `Booking_ID` - string partition key
- `Booking_DateTime` - string sort key, stored as `YYYY-MM-DD HH:MM`
- `customer_name` - string, also GSI partition key
- `party_size` - number
- `special_requests` - optional string

## Function 1: createbooking

```json
{
  "name": "createbooking",
  "description": "Create a new R-Cafe table reservation. Backend Lambda normalizes customer-style date and time values before storing clean DynamoDB data.",
  "parameters": {
    "customer_name": {
      "description": "Real customer name for the reservation. Do not use placeholders like User, Guest, Customer, John Doe, Test, or repeated junk text.",
      "required": "True",
      "type": "string"
    },
    "party_size": {
      "description": "Number of guests for the reservation. Standard automatic bookings support 1 to 12 guests. More than 12 requires manager approval.",
      "required": "True",
      "type": "string"
    },
    "booking_date": {
      "description": "Requested reservation date. Accept natural/customer formats such as tomorrow, tomorow, day after, 27/7, 27 July, July 27, 27th July, or YYYY-MM-DD. Backend Lambda normalizes to YYYY-MM-DD and validates the one-month booking window.",
      "required": "True",
      "type": "string"
    },
    "booking_time": {
      "description": "Requested reservation time. Accept customer formats such as 7pm, 7 pm, 7.00pm, 19:00, or 7:30 PM. Backend Lambda normalizes to 24-hour HH:MM. Bare hours like 9 require AM/PM clarification.",
      "required": "True",
      "type": "string"
    },
    "specialRequests": {
      "description": "Compact seating or accessibility notes for the reservation, such as kids, elderly guests, wheelchair access, high chair, stroller space, quiet seating, near-entrance seating, parking assistance, or drop-off assistance. Use none if the customer has no special requests.",
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
  "description": "Retrieve an existing R-Cafe reservation using Booking ID plus reservation date and time.",
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

AWS allows a maximum of 5 parameters per function, so this uses the compact update schema.

```json
{
  "name": "updateBooking",
  "description": "Update an existing R-Cafe reservation. Use bookingId, bookingDate, and bookingTime to locate the reservation when known. Use updateType and newValue to describe the requested change.",
  "parameters": {
    "bookingId": {
      "description": "The unique booking ID for the reservation being updated. If unknown, leave empty and include the existing customer name in newValue when possible.",
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
      "description": "The new value for the requested update. For time use customer time or HH:MM. For date use customer date or YYYY-MM-DD. For partySize use a number. For name use the new customer name. For specialRequests use compact seating/accessibility notes. If Booking ID is unknown, include the existing customer name too, for example: 22:00 name Anna.",
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
  "description": "Delete/cancel an existing R-Cafe reservation after the agent has confirmed the exact booking with the customer.",
  "parameters": {
    "bookingId": {
      "description": "The unique booking ID to delete.",
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
  "description": "Find R-Cafe reservations by customer name using the r-cafe-index DynamoDB GSI.",
  "parameters": {
    "customerName": {
      "description": "Existing customer name to search. Use when the customer does not remember the Booking ID or wants to find booking details by name.",
      "required": "True",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```


---

# Continuous Upgrade: Function JSON Blocks For AWS Console

Use the following JSON blocks in this sequence when updating the Bedrock action group function details.

## 1. createbooking

```json
{
  "name": "createbooking",
  "description": "Create a new R-Cafe table reservation. Backend Lambda normalizes customer-style date and time values before storing clean DynamoDB data.",
  "parameters": {
    "customer_name": {
      "description": "Real customer name for the reservation. Do not use placeholders like User, Guest, Customer, John Doe, Test, Unknown, or repeated junk text.",
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

## 2. getBooking

```json
{
  "name": "getBooking",
  "description": "Retrieve an existing R-Cafe reservation using Booking ID plus reservation date and time.",
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

## 3. updateBooking

```json
{
  "name": "updateBooking",
  "description": "Update an existing R-Cafe reservation. Use bookingId, bookingDate, and bookingTime to locate the reservation when known. Use updateType and newValue to describe the requested change. This compact schema stays within the AWS 5-parameter limit.",
  "parameters": {
    "bookingId": {
      "description": "The unique booking ID for the reservation being updated. If unknown, leave empty and include the existing customer name in newValue when possible.",
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
      "description": "The new value for the requested update. For time use customer time or HH:MM. For date use customer date or YYYY-MM-DD. For partySize use a number. For name use the new customer name. For specialRequests use compact seating/accessibility notes. If Booking ID is unknown, include the existing customer name too, for example: 22:00 name Anna.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```

## 4. deleteBooking

```json
{
  "name": "deleteBooking",
  "description": "Delete or cancel an existing R-Cafe reservation after the agent has confirmed the exact booking with the customer.",
  "parameters": {
    "bookingId": {
      "description": "The unique booking ID to delete.",
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

## 5. findBookingByName

```json
{
  "name": "findBookingByName",
  "description": "Find R-Cafe reservations by customer name using the r-cafe-index DynamoDB GSI.",
  "parameters": {
    "customerName": {
      "description": "Existing customer name to search. Use when the customer does not remember the Booking ID or wants to find booking details by name.",
      "required": "True",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
```
