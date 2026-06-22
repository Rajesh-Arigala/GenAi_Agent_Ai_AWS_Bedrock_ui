# R-Cafe Architecture Responsibilities

This document organizes what belongs in each layer of the R-Cafe Bedrock Agent system before the final implementation pass.

## 1. UI Layer

Purpose: customer experience only. The UI is not the business source of truth.

What belongs here:
- Clean customer-facing chat interface.
- Mobile-friendly layout.
- Language selector: English plus top spoken Indian-language options: Hindi, Bengali, Marathi, Telugu, Tamil. Kannada may remain as an additional regional option.
- Dummy location only, with no GPS permission popup.
- Send context to frontend Lambda:
  - `preferredLanguage`
  - `languageName`
  - `locale`
  - `timezone`
  - `deviceType`
  - `screenSize`
  - dummy location fields
  - accessibility support enabled
- Same-message retry UI for API/network errors.
- Hide backend details from customers.
- Do not show Agent ID, Alias ID, API Gateway URL, session internals, traces, or AWS terms.

What does not belong here:
- Date parsing truth.
- Booking validation.
- DynamoDB logic.
- Manager workflow truth.

## Language Support

The UI should include English plus top Indian and top international language options for customer convenience.

Top Indian-language options:
- Hindi
- Bengali
- Marathi
- Telugu
- Tamil

Additional regional option:
- Kannada

Top international-language options:
- Spanish
- Chinese
- Arabic
- French
- Portuguese

The selected language should be passed through `preferredLanguage` and `languageName`; the agent should also follow the customer's latest typed language.

## 2. Frontend Lambda Layer

Purpose: API Gateway bridge to Bedrock Agent.

What belongs here:
- Receive requests from the Render UI.
- Preserve the customer query exactly as typed.
- Generate trusted server-side current date/time using `Asia/Kolkata`.
- Forward Bedrock `sessionState` correctly:
  - `sessionAttributes`
  - `promptSessionAttributes`
- Add context:
  - `currentDate`
  - `currentTime`
  - `currentWeekday`
  - `currentYear`
  - `timezone`
  - `preferredLanguage`
  - `managerPhone: 9916437369`
  - `managerWhatsApp: 9916437369`
  - `phoneValidationRule`
  - `specialRequestsSupported`
  - `accessibilityCapture`
- Invoke `bedrock-agent-runtime.invoke_agent`.
- Return the agent response to the UI.

What does not belong here:
- Booking creation/update/delete logic.
- DynamoDB writes.
- Final customer booking date parsing truth.
- Hidden/fake context inserted into `inputText`.

## 3. System Prompt Layer

Purpose: conversation behavior and tool-use discipline.

What belongs here:
- Agent name: `R-Cafe Visit Planner Agent`.
- Tone and customer-facing behavior.
- Slot-filling rules.
- Ask one question at a time.
- Use current date from Bedrock session attributes or prompt session attributes.
- Never say today's date is private, a security issue, or blocked by internal policy.
- Language behavior.
- Ask about special needs:
  - children/kids
  - elderly guests
  - wheelchair users
  - physically disabled guests
  - high chair
  - stroller space
  - quiet seating
  - near-entrance seating
  - parking/drop-off assistance
- Large-party behavior:
  - More than 12 guests requires manager approval.
  - Do not create an automatic booking.
  - Offer call/WhatsApp: `9916437369`.
  - Future ticket/callback workflow is not live yet.
- Delete safety:
  - Find booking first if Booking ID is unknown.
  - Confirm the exact booking before deletion.
- Update safety:
  - Reuse the latest confirmed Booking ID in the conversation.
  - The same Booking ID should survive date/time/name/party-size updates.
- AWS 5-parameter constraint:
  - `updateBooking`: `bookingId`, `bookingDate`, `bookingTime`, `updateType`, `newValue`.

What does not belong here:
- Final data validation.
- Trusting model-only date parsing.
- Inventing booking IDs.
- Pretending future RAG/weather/search/ticketing is active.

## 4. Backend Action Lambda Layer

Purpose: source of truth before DynamoDB.

What belongs here:
- All DynamoDB operations:
  - `createbooking`
  - `getBooking`
  - `updateBooking`
  - `deleteBooking`
  - `findBookingByName`
- Deterministic validation:
  - party size must be at least 1
  - party size greater than 12 returns escalation, not booking
  - operating hours are 11:00 to 23:00
  - no past booking
  - one-month rolling booking window
  - real customer name, not `User`, `John Doe`, `eeeee`, or similar placeholders
- Deterministic date/time normalization:
  - `tomorrow`
  - `tomorow`
  - `day after`
  - `27/7`
  - `17th july`
  - `17 july 2026`
  - weekdays
  - `9pm`, `9 pm`, `9.00pm`, `21:00`
  - reject bare `9` with an AM/PM clarification
- Store clean DynamoDB data:
  - `Booking_ID`
  - `Booking_DateTime`
  - `customer_name`
  - `party_size`
  - `special_requests`
- Preserve the same Booking ID during updates.
- Use GSI `r-cafe-index` for customer-name lookup.
- Never write planner/internal text into DynamoDB.

What does not belong here:
- Chat tone.
- Language translation.
- UI behavior.
- Frontend API Gateway response styling.



## Date And Month Permutations

For the current R-Cafe booking project, the default booking year is fixed to `2026` whenever the customer does not explicitly provide a year. This comes from the current system/session date during this test cycle.

The system must support common date/month permutations before storing data:
- `27/7` -> `2026-07-27`
- `27-7` -> `2026-07-27`
- `07/27/2026` only if clearly provided in a US-style context; otherwise prefer Indian `DD/MM` interpretation.
- `27/07/2026` -> `2026-07-27`
- `2026-07-27` -> `2026-07-27`
- `27 July` -> `2026-07-27`
- `27 Jul` -> `2026-07-27`
- `July 27` -> `2026-07-27`
- `Jul 27` -> `2026-07-27`
- `27th July` -> `2026-07-27`
- `the 27th of July` -> `2026-07-27`
- `tomorrow`, `tomorow`, `day after`, weekdays, and short weekdays must be resolved from `currentDate`.

Do not roll unresolved dates into `2027`. If a 2026 date is already past or outside the one-month booking window, say exactly that and ask for a valid date within the allowed window.

## Stack Synchronization Contract

The UI, frontend Lambda, Bedrock action-group functions, function parameters, backend action Lambda, and DynamoDB table must stay in sync.

Live action-group functions and parameters:

### `createbooking`
- `customer_name` string, required
- `party_size` string/number, required
- `booking_date` string, required; backend Lambda accepts natural/date permutations and stores normalized `YYYY-MM-DD`
- `booking_time` string, required; backend Lambda accepts common time permutations and stores normalized `HH:MM`
- `specialRequests` string, optional

### `getBooking`
- `bookingId` string, required
- `bookingDate` string, required; backend Lambda normalizes before lookup
- `bookingTime` string, required; backend Lambda normalizes before lookup

### `updateBooking`
AWS 5-parameter compact schema:
- `bookingId` string, optional if lookup by name is used
- `bookingDate` string, required when identifying current booking by date/time
- `bookingTime` string, required when identifying current booking by date/time
- `updateType` string, required; allowed values: `time`, `date`, `partySize`, `name`, `specialRequests`
- `newValue` string, required; new value for update, may include customer lookup name if Booking ID is unknown

### `deleteBooking`
- `bookingId` string, required
- `bookingDate` string, required
- `bookingTime` string, required

### `findBookingByName`
- `customerName` string, required

DynamoDB clean storage fields:
- `Booking_ID` string partition key
- `Booking_DateTime` string sort key, format `YYYY-MM-DD HH:MM`
- `customer_name` string
- `party_size` number
- `special_requests` string, optional

## Main Issue To Fix Once For All

The date problem exists because date parsing is still too dependent on Bedrock.

The final architecture should be:

```text
Prompt guides date handling.
Frontend Lambda supplies current date.
Backend Lambda normalizes and validates final date/time.
DynamoDB only receives clean normalized values.
```

## Final Implementation Direction

1. Keep UI focused on customer experience and context collection.
2. Keep frontend Lambda focused on Bedrock invocation and trusted session context.
3. Keep system prompt focused on conversation rules and tool-use discipline.
4. Move final date/time normalization and validation into backend action Lambda.
5. Store special requests in `special_requests` on the same DynamoDB booking item.
6. Keep manager ticketing/callback as a future workflow until an actual backend function exists.
