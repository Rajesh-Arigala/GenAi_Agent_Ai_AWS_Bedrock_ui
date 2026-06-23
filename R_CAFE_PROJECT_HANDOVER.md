# R-Cafe Visit Planner Agent - Project Handover

Last updated: 2026-06-23

This document is a handover summary for continuing the R-Cafe Bedrock Agent project in a new session. It captures the architecture, decisions, bugs found, fixes made, AWS updates required, current working behavior, and next steps.

## Project Folder

`/Users/jhonny001/Desktop/GenAi Notes/Final_GenAi/Ai Agents/AWS/GenAi_Agent_Ai_AWS_Bedrock_ui`

Important files:

- `lambda/bedrock_agent_lambda.py` - backend/action-group Lambda for DynamoDB reservation operations.
- `frontend_lambda/lambda_function.py` - frontend/API Gateway Lambda that invokes the Bedrock Agent.
- `ui/app.py` - Render Flask app entry point.
- `ui/templates/index.html` - customer-facing web UI.
- `systme-prompt.md` - current compact AWS Bedrock Agent instruction prompt. The filename is misspelled in the repo but this is the active prompt file.
- `Action_group_funtions.md` - consolidated AWS Bedrock action-group function reference. The filename is misspelled in the repo but this is the active action-group reference.
- `R_CAFE_LAYER_RESPONSIBILITIES.md` - layer responsibility/architecture notes.
- `features_in_lambda.md` - Lambda feature reference.

## Current AWS Resources

- AWS Region: `us-east-1`
- Bedrock Agent ID: `YZTK3R4TM6`
- Bedrock Agent Alias ID: `TSTALIASID`
- DynamoDB table: `Restro-Table_booking-R-Cafe`
- Main table key:
  - Partition key: `Booking_ID`
  - Sort key: `Booking_DateTime`
- DynamoDB GSI:
  - Index name: `r-cafe-index`
  - Partition key: `customer_name`
  - Sort key: `Booking_DateTime`
- Manager call/WhatsApp number: `9916437369`
- Render UI: `https://genai-agent-ai-aws-bedrock-ui.onrender.com`

## Current Product Scope

The live system is a single Bedrock Agent connected to one action-group Lambda. The agent currently supports table reservation flows only.

Current live capabilities:

1. Create booking.
2. Find booking by Booking ID/date/time.
3. Find booking by customer name.
4. Update booking.
5. Delete booking.
6. Preserve special requests.
7. Escalate large-party requests.
8. Suggest close name matches for typo/partial-name lookup.

Future capabilities discussed but not live yet:

- S3/RAG menu retrieval.
- Menu combo and per-head price comparison.
- Local places to visit near R-Cafe.
- Weather-aware suggestions.
- Clothing suggestions for weather.
- Multi-agent architecture.
- Login/signup via phone/email/Google.
- OTP/email acknowledgement.
- Long-term memory and entity anchors.
- Manager ticket workflow and automated callbacks.
- Mobile app.
- Branding as a one-day R-Cafe visit/trip planner.

Branding changes were intentionally postponed. Functionality is the priority.

## Architecture Layers

### UI Layer

The UI is for customer interaction and Render hosting. It should not show backend internals. It should eventually hide implementation fields from customers.

Current UI responsibilities:

- Chat interface.
- Session ID creation/loading.
- Send query to API Gateway/frontend Lambda.
- Send dynamic context/session attributes.
- Store current active booking anchors from successful responses.
- Keep latest conversation turns and a lightweight older-turn summary.
- Handle API/network errors in the same message context rather than producing noisy repeated error bubbles.

Important UI context passed:

- `currentDate`
- `currentTime`
- `currentWeekday`
- `currentTimestamp`
- `currentTimestampUtc`
- `timezone`
- `locale`
- `preferredLanguage`
- dummy location context, no GPS permission popup
- `activeBookingId`
- `activeBookingDate`
- `activeBookingTime`
- `activeBookingCustomerName`
- `activeBookingPartySize`
- `activeBookingStatus`
- `recentConversationTurns`
- `conversationSummary`

### Frontend Lambda Layer

File: `frontend_lambda/lambda_function.py`

Purpose:

- API Gateway receives UI request.
- Frontend Lambda invokes Bedrock Agent Runtime.
- It forwards `sessionState` to Bedrock.
- It adds current timestamp/context attributes.
- It returns the agent response to UI.

Current conclusion:

- Frontend Lambda is needed because the UI cannot securely call Bedrock Agent Runtime directly.
- It is also the right place to inject current date/time and session metadata.
- It was already forwarding session attributes correctly.

### Bedrock Agent Prompt Layer

File: `systme-prompt.md`

Purpose:

- Defines customer conversation behavior.
- Defines slot-filling rules.
- Defines date/time interpretation rules.
- Defines manager escalation and late-arrival policy.
- Defines close-match confirmation behavior.

Important AWS constraint:

- Bedrock Agent Instructions have a 20,000 character limit.
- The old prompt became about 44,305 characters and AWS rejected it.
- The current compact prompt is about 13,063 characters and fits the limit.

### Backend Action-Group Lambda Layer

File: `lambda/bedrock_agent_lambda.py`

Purpose:

- Final deterministic validation.
- Normalize date/time before DynamoDB.
- Enforce booking window and operating hours.
- Enforce party size rules.
- Enforce valid customer names.
- Write/read/update/delete DynamoDB records.
- Return clean customer-facing result text to Bedrock.
- Implement closest-name matching.

### DynamoDB Layer

Table: `Restro-Table_booking-R-Cafe`

Important fields:

- `Booking_ID`
- `Booking_DateTime`
- `customer_name`
- `party_size`
- `booking_status`
- `special_requests`

Status values:

- `active` - current valid booking.
- `closed-executed` - past/historical executed booking.
- `invalid` - loose/wasted/incomplete records.

Only valid active bookings in the one-month window should be presented to customers.

## Major Issues Found and Resolved

### 1. Bedrock Model Leaking Tool Syntax

Observed with Nova Lite:

- `Action: user__askuser(...)`
- `Question: ... </tool>`
- fake tool syntax instead of natural customer response.

Resolution:

- Prompt was tightened.
- Model was switched to Nova Pro.
- Nova Pro stopped leaking tool syntax in the latest tests.

### 2. Prompt Too Large for AWS

AWS error:

- `max-instruction-size` limit is 20,000.
- Old prompt requested about 35k+ characters.

Resolution:

- Rewrote prompt into compact final version in `systme-prompt.md`.
- Current prompt is around 13k characters.

### 3. Date/Time Interpretation Was Unreliable

Problems seen:

- `tomorrow` not resolved.
- `27/7` incorrectly called past.
- no-year dates were mishandled.
- bare hours like `9` were accepted without AM/PM.
- model did not know current date.

Resolution:

- UI/frontend Lambda now pass current date/time context.
- Prompt tells agent to use session attributes.
- Backend Lambda deterministically normalizes dates/times.
- Default year is 2026.
- Booking window is one month from current date.
- No silent rollover to 2027.
- Bare hour requires AM/PM unless context is clear.

### 4. Active Booking Memory Was Weak

Problems seen:

- Agent repeatedly asked for Booking ID even after creating a booking.
- Updates created new bookings instead of modifying the existing booking.
- User forgot Booking ID and the agent got stuck.

Resolution:

- UI stores active booking anchors.
- Prompt instructs agent to reuse same-session active booking context.
- Backend supports update by exact name and now close-match suggestions.

### 5. Placeholder/Junk DynamoDB Records

Problems seen:

- Records with `User`, `None`, internal planner text, missing values, or bad names.
- Loose booking IDs were created from incomplete inputs.

Resolution:

- Backend validates names.
- Requires first and last name for standard booking.
- Rejects placeholders like `User`, `Customer`, `Guest`, `John Doe`, `Test`, etc.
- Adds `booking_status` and validates active records.

### 6. Special Requests Were Not Preserved

Problems discussed:

- Kids, elderly guests, parking assistance, ramp, infant chair, physically disabled guests need to be captured.
- Repeated updates must preserve earlier special requests.

Resolution:

- `specialRequests` added to create booking.
- `updateBooking` supports `updateType=specialRequests`.
- Prompt instructs the agent to keep a compact running summary.
- Backend stores `special_requests`.

### 7. Large Party Escalation

Rule:

- Standard automatic bookings support up to 12 guests.
- More than 12 requires manager approval.

Resolution:

- Backend returns escalation response for party size > 12.
- Prompt tells agent not to create confirmed bookings for >12.
- Manager number is `9916437369`.
- Indian callback number should be 10 digits.

### 8. Late Arrival / Customer Retention Policy

Discussion outcome:

- Hard rejection after 23:00 is bad hospitality.
- Normal reservation hours remain 11:00 to 23:00.
- If the guest may arrive after 23:00 but by 23:20, R-Cafe can try to hold the table briefly as a courtesy.
- Service after 23:00 may be limited.
- Do not update official booking time beyond 23:00.
- Store a late-arrival note in special requests.
- After 23:20, manager approval is required for table hold and limited food options.
- If customer is driving, prioritize road safety and recommend a passenger call/WhatsApp or pulling over safely.

### 9. Exact Name Lookup Was Too Fragile

Problem:

- Booking was under a misspelled name like `debmalya chnadra`.
- Searching `debmalya chandra` failed.
- Agent falsely said no booking under the name.

Resolution:

- Backend now performs exact GSI query first.
- If exact query fails, backend performs closest-name fallback.
- Matching uses normalized text, first-name/last-name match, and fuzzy similarity.
- Threshold is 50%.
- Returns top 3 close matches.
- Close matches are confirmation-gated.

Example desired response:

`No exact active booking was found for the name "arigala". However, a close match was found: ID R-0B4F8E on 2026-06-23 at 21:00 for Rajesh Arigala with party size 12. Is this your booking?`

## Current Lambda Backend Features

Implemented in `lambda/bedrock_agent_lambda.py`:

- Deterministic date parsing.
- Deterministic time parsing.
- One-month booking window.
- Business hours validation.
- Large-party escalation.
- Customer name validation.
- Placeholder/internal-text rejection.
- `booking_status` validation.
- Active booking filtering.
- `special_requests` persistence.
- Compact update schema support.
- Exact name query via `r-cafe-index`.
- Fuzzy/closest name fallback via scan.
- Confirmation-required close match response.
- Syntax compile passed.

## Current Action Group Functions

Reference file: `Action_group_funtions.md`

### `createbooking`

Parameters:

- `customer_name`
- `party_size`
- `booking_date`
- `booking_time`
- `specialRequests`

### `getBooking`

Parameters:

- `bookingId`
- `bookingDate`
- `bookingTime`

### `updateBooking`

Compact 5-parameter schema due AWS function parameter limit:

- `bookingId`
- `bookingDate`
- `bookingTime`
- `updateType`
- `newValue`

Allowed update types:

- `time`
- `date`
- `partySize`
- `name`
- `specialRequests`

### `deleteBooking`

Parameters:

- `bookingId`
- `bookingDate`
- `bookingTime`

### `findBookingByName`

Parameters:

- `customerName`

Behavior:

- Exact/case-tolerant query through `r-cafe-index`.
- If exact lookup fails, closest-name suggestions are returned.
- Suggestions must be confirmed by customer before update/delete/review.

## Required AWS IAM Policy

The backend action-group Lambda execution role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:825187895465:table/Restro-Table_booking-R-Cafe",
        "arn:aws:dynamodb:us-east-1:825187895465:table/Restro-Table_booking-R-Cafe/index/r-cafe-index"
      ]
    }
  ]
}
```

`dynamodb:Scan` is required for closest-name fallback. Exact lookup only needs `Query`, but fuzzy matching cannot be done through the DynamoDB partition key alone.

## Testing Results

### Working Well

Recent tests confirmed:

- 13 guests triggers manager escalation.
- Correcting 13 to 12 creates a booking.
- Active booking memory works.
- Time update works without asking for Booking ID again.
- Name correction works.
- Special requests are preserved.
- Exact name lookup works.
- Close-match fallback works after adding Scan permission.
- Last-name partial lookup like `arigala` can find `Rajesh Arigala` as a close match.
- The agent asks for confirmation before treating the close match as the customer's booking.

### Latest Good Test

User:

`Update booking details.`

Agent asked for ID/date/time/update details.

User:

`I don have the id`

Agent asked for first and last name.

User:

`arigala`

Agent response:

`No exact active booking was found for the name "arigala". However, a close match was found: ID: R-0B4F8E on 2026-06-23 at 21:00 for Rajesh Arigala with a party size of 12 and special requests for 2 elders and 3 infants. Is this your booking?`

This is the desired behavior.

### Remaining Prompt Polish

Minor wording still seen:

- Agent said: `the type of update the user wants to make`.
- Better: `the type of update you want to make`.

This is prompt/style polish, not a backend failure.

## AWS Update Order

When deploying changes to AWS:

1. Update backend Lambda code from `lambda/bedrock_agent_lambda.py`.
2. Ensure backend Lambda execution role has `dynamodb:Scan`.
3. Update Bedrock Agent instructions from `systme-prompt.md`.
4. Ensure action-group descriptions match `Action_group_funtions.md`.
5. Save Bedrock Agent.
6. Prepare the Bedrock Agent.
7. Test exact lookup and fuzzy lookup.

## Known Caveats

- Fuzzy fallback uses Scan, which is acceptable for demo/prototype scale but not ideal for production at high volume.
- Production should add normalized name fields or login-based identity.
- Login/signup is future architecture and should not be implemented before demo stability.
- Name fuzzy match is a suggestion, not proof of identity.
- Close matches must be confirmed before update/delete.
- UI customer screen still shows some technical/session fields; customer-facing polish is future work.
- Branding is intentionally not updated yet.

## Future Architecture Direction

For production-grade identity and memory:

- Add login/signup using phone, email, or Google.
- Verify phone/email via OTP or email acknowledgement.
- Tie bookings to user account ID instead of customer name.
- Keep session memory for the current chat.
- Store long-term summarized memory under account identity.
- Use entity anchors for active booking, customer profile, phone/email, and preferences.
- Keep fuzzy name matching as convenience only, not authorization.

For future multi-agent architecture:

- Reservation agent.
- Menu/RAG agent.
- Local visit planner agent.
- Weather/clothing agent.
- Manager escalation/ticket agent.
- Communication agent for WhatsApp/calls/SMS after approval.

## Next Recommended Work

1. Test close-match flow end-to-end:
   - search typo name
   - confirm suggested booking
   - update time/date/special request

2. Improve prompt wording:
   - replace "the user" with "you" in customer-facing update prompts.

3. Add UI protection if not already complete:
   - strip leaked `Action:`, `Question:`, `<tool>`, `</tool>` if a weaker model is used again.

4. Clean customer-facing UI:
   - hide Agent ID, Alias ID, API Gateway, and session internals from real customers.

5. Decide whether to keep using Nova Pro for reliability.

6. Later, revisit branding and one-day R-Cafe visit planner positioning.

## Current Status Summary

The project has moved from a fragile booking demo to a much more stable prototype:

- Date/time handling is deterministic.
- Current date context is available.
- Session booking anchors work.
- Special needs are captured.
- Large-party and late-arrival policies are customer-friendly.
- Name typo lookup now works through closest-match fallback.
- Prompt fits AWS instruction limits.
- DynamoDB and action-group functions are aligned.

The next session should start from this document, not the full chat history.
