import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import boto3

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")

DEFAULT_AGENT_ID = os.environ.get("BEDROCK_AGENT_ID", "")
DEFAULT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID")
RESTAURANT_TIMEZONE = os.environ.get("RESTAURANT_TIMEZONE", "Asia/Kolkata")
MANAGER_CONTACT = os.environ.get("MANAGER_CONTACT", "9916437369")


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(body),
    }


def _parse_body(event):
    body = event.get("body")
    if not body:
        return {}
    if isinstance(body, dict):
        return body
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _now_parts(timezone_name):
    try:
        tz = ZoneInfo(timezone_name or RESTAURANT_TIMEZONE)
    except Exception:
        tz = ZoneInfo(RESTAURANT_TIMEZONE)
    now = datetime.now(tz)
    return {
        "currentDate": now.strftime("%Y-%m-%d"),
        "currentTime": now.strftime("%H:%M"),
        "currentWeekday": now.strftime("%A"),
        "currentYear": str(now.year),
        "currentTimestamp": now.isoformat(),
        "currentTimestampUtc": datetime.now(timezone.utc).isoformat(),
        "timezone": str(tz),
    }


def _prepare_session_state(raw_session_state):
    session_state = _as_dict(raw_session_state).copy()
    session_attributes = _as_dict(session_state.get("sessionAttributes")).copy()
    prompt_session_attributes = _as_dict(session_state.get("promptSessionAttributes")).copy()

    timezone_name = session_attributes.get("timezone") or prompt_session_attributes.get("timezone") or RESTAURANT_TIMEZONE
    now_values = _now_parts(timezone_name)

    shared_context = {
        **now_values,
        "application": "r-cafe-render-ui",
        "channel": "web",
        "restaurantTimezone": RESTAURANT_TIMEZONE,
        "managerPhone": MANAGER_CONTACT,
        "managerWhatsApp": MANAGER_CONTACT,
        "bookingWindow": "one month from currentDate",
        "phoneCountry": "IN",
        "phoneValidationRule": "10_digits_starts_6_7_8_9_optional_91",
        "locationMode": session_attributes.get("locationMode", "dummy"),
        "locationPermissionRequired": session_attributes.get("locationPermissionRequired", "false"),
        "gpsUsed": session_attributes.get("gpsUsed", "false"),
        "specialRequestsSupported": "true",
        "accessibilityCapture": "enabled",
    }

    # UI-provided values win for user preference fields, while server date/time wins for trust.
    preferred_context = {
        "locale": session_attributes.get("locale", prompt_session_attributes.get("locale", "en-IN")),
        "preferredLanguage": session_attributes.get("preferredLanguage", prompt_session_attributes.get("preferredLanguage", "en-IN")),
        "languageName": session_attributes.get("languageName", prompt_session_attributes.get("languageName", "English")),
        "deviceType": session_attributes.get("deviceType", prompt_session_attributes.get("deviceType", "web")),
        "screenSize": session_attributes.get("screenSize", prompt_session_attributes.get("screenSize", "unknown")),
        "locationLabel": session_attributes.get("locationLabel", prompt_session_attributes.get("locationLabel", "R-Cafe primary branch")),
        "locationCity": session_attributes.get("locationCity", prompt_session_attributes.get("locationCity", "Not collected")),
    }

    final_context = {**preferred_context, **shared_context}
    session_attributes.update(final_context)
    prompt_session_attributes.update(final_context)

    session_state["sessionAttributes"] = session_attributes
    session_state["promptSessionAttributes"] = prompt_session_attributes
    return session_state


def _collect_agent_response(agent_response, include_trace=False):
    final_text = ""
    traces = []

    for event in agent_response.get("completion", []):
        if "chunk" in event:
            chunk = event["chunk"]
            if "bytes" in chunk:
                final_text += chunk["bytes"].decode("utf-8")
        if include_trace and "trace" in event:
            traces.append(event["trace"])

    result = {"response": final_text.strip() or "No response received from the agent."}
    if include_trace:
        result["trace"] = traces
    return result


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod")
    if method == "OPTIONS":
        return _response(200, {"ok": True})

    try:
        data = _parse_body(event)
        query = data.get("query", "").strip()
        session_id = data.get("session_id", "").strip()
        agent_id = data.get("agent_id", DEFAULT_AGENT_ID).strip()
        alias_id = data.get("alias_id", DEFAULT_ALIAS_ID).strip()
        enable_trace = bool(data.get("enable_trace", False))

        if not query:
            return _response(400, {"error": "Query cannot be empty."})
        if not session_id:
            return _response(400, {"error": "Session ID is required."})
        if not agent_id:
            return _response(400, {"error": "Agent ID is required."})

        prepared_session_state = _prepare_session_state(data.get("session_state") or {})

        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=session_id,
            inputText=query,
            enableTrace=enable_trace,
            sessionState=prepared_session_state,
        )

        result = _collect_agent_response(response, include_trace=enable_trace)
        result["session_id"] = session_id
        return _response(200, result)

    except bedrock_agent_runtime.exceptions.ResourceNotFoundException:
        return _response(404, {"error": "Bedrock Agent or alias was not found. Check agent_id and alias_id."})
    except bedrock_agent_runtime.exceptions.AccessDeniedException:
        return _response(403, {"error": "Lambda does not have permission to invoke this Bedrock Agent."})
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        return _response(500, {"error": f"Failed to invoke Bedrock Agent: {str(e)}"})
