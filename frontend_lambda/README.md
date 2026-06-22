# R-Cafe Frontend Lambda

This Lambda sits behind API Gateway and invokes the Amazon Bedrock Agent.

Responsibilities:
- Accept requests from the Render UI.
- Preserve the customer query exactly as typed.
- Build trusted `sessionState.sessionAttributes` and `sessionState.promptSessionAttributes`.
- Inject server-side current date/time in `Asia/Kolkata` so relative dates like `tomorrow` are stable.
- Forward language, device, dummy location, manager contact, phone validation, and accessibility context.
- Return the Bedrock Agent response to the UI.

Environment variables:
- `BEDROCK_AGENT_ID`
- `BEDROCK_AGENT_ALIAS_ID` defaults to `TSTALIASID`
- `RESTAURANT_TIMEZONE` defaults to `Asia/Kolkata`
- `MANAGER_CONTACT` defaults to `9916437369`
