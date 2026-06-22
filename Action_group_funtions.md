{
  "name": "createbooking",
  "description": "Create a new table reservation at the restaurant.",
  "parameters": {
    "booking_date": {
      "description": "The reservation date in YYYY-MM-DD format.",
      "required": "False",
      "type": "string"
    },
    "party_size": {
      "description": "The number of guests.",
      "required": "False",
      "type": "string"
    },
    "booking_time": {
      "description": "The reservation time in HH-MM format.",
      "required": "False",
      "type": "string"
    },
    "customer_name": {
      "description": "The full name of the customer.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}

{
  "name": "getBooking",
  "description": "Retrieve reservation details using a booking ID, date, time, and party size.",
  "parameters": {
    "bookingTime": {
      "description": "The reservation time in HH-MM format.",
      "required": "False",
      "type": "string"
    },
    "bookingDate": {
      "description": "The reservation date in YYYY-MM-DD format.",
      "required": "False",
      "type": "string"
    },
    "partySize": {
      "description": "The number of guests.",
      "required": "False",
      "type": "string"
    },
    "bookingId": {
      "description": "The unique booking ID.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}

{
  "name": "updateBooking",
  "description": "Modify an existing table reservation details.",
  "parameters": {
    "newTime": {
      "description": "The new requested time in HH-MM format if changing.",
      "required": "False",
      "type": "string"
    },
    "currentDateTime": {
      "description": "The current combined date and time string to locate the item.",
      "required": "False",
      "type": "string"
    },
    "newDate": {
      "description": "The new requested date in YYYY-MM-DD format if changing.",
      "required": "False",
      "type": "string"
    },
    "partySize": {
      "description": "The updated number of guests if changing.",
      "required": "False",
      "type": "string"
    },
    "bookingId": {
      "description": "The unique booking ID.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}

{
  "name": "deleteBooking",
  "description": "Cancel a restaurant table booking by its ID and reservation date-time.",
  "parameters": {
    "bookingTime": {
      "description": "The reservation time in HH-MM format.",
      "required": "False",
      "type": "string"
    },
    "bookingDate": {
      "description": "The reservation date in YYYY-MM-DD format.",
      "required": "False",
      "type": "string"
    },
    "bookingId": {
      "description": "The unique booking ID.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}

{
  "name": "findBookingByName",
  "description": "Look up a customer's booking ID and reservation date-time details using their full name.",
  "parameters": {
    "customerName": {
      "description": "The full name of the customer who made the reservation.",
      "required": "False",
      "type": "string"
    }
  },
  "requireConfirmation": "DISABLED"
}

