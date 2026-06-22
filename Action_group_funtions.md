{
  "name": "updateBooking",
  "description": "Modify an existing table reservation details.",
  "parameters": {
    "bookingDate": {
      "description": "The current/original reservation date in YYYY-MM-DD format. If the current conversation has a confirmed booking, reuse its current date silently.",
      "required": "False",
      "type": "string"
    },
    "bookingTime": {
      "description": "The current/original reservation time in 24-hour HH:MM format. If the current conversation has a confirmed booking, reuse its current time silently.",
      "required": "False",
      "type": "string"
    },
    "bookingId": {
      "description": "The unique booking ID.",
      "required": "False",
      "type": "string"
    },
    "customerLookupName": {
      "description": "Existing customer name used to find the reservation when the customer does not remember the Booking ID. Use for lookup only, not for changing the booking name.",
      "required": "False",
      "type": "String"
    },
    "customerName": {
      "description": "New customer name if the customer wants to change the booking name. Omit if the name is not changing.",
      "required": "False",
      "type": "String"
    },
    "newDate": {
      "description": "New requested reservation date in YYYY-MM-DD format if changing the date. Omit if the date is not changing.",
      "required": "False",
      "type": "String"
    },
    "newTime": {
      "description": "New requested reservation time in 24-hour HH:MM format if changing the time. Omit if the time is not changing.",
      "required": "False",
      "type": "String"
    },
    "partySize": {
      "description": "Updated number of guests if changing party size. Omit if party size is not changing.",
      "required": "False",
      "type": "String"
    }
  },
  "requireConfirmation": "DISABLED"
}


============
This is a 5 parameter schema

{
  "name": "updateBooking",
  "description": "Update an existing R-Cafe reservation. Use bookingId, bookingDate, and bookingTime to locate the reservation when known. Use updateType and newValue to describe the requested change.",
  "parameters": {
    "bookingId": {
      "description": "The unique booking ID for the reservation being updated. If unknown, leave empty and include the customer name in newValue.",
      "required": "False",
      "type": "string"
    },
    "bookingDate": {
      "description": "The current/original reservation date in YYYY-MM-DD format.",
      "required": "False",
      "type": "string"
    },
    "bookingTime": {
      "description": "The current/original reservation time in 24-hour HH:MM format.",
      "required": "False",
      "type": "string"
    },
    "updateType": {
      "description": "The type of update requested. Allowed values: time, date, partySize, name.",
      "required": "False",
      "type": "string"
    },
    "newValue": {
      "description": "The new value for the requested update. For time use HH:MM. For date use YYYY-MM-DD. For partySize use a number. For name use the new customer name. If Booking ID is unknown, include the existing customer name too.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}
