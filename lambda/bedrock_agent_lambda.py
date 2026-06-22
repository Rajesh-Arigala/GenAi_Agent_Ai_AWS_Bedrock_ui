import json
import uuid
import os
import calendar
import re
import boto3
from datetime import datetime, date
from zoneinfo import ZoneInfo
from boto3.dynamodb.conditions import Key

# --- BUSINESS POLICY CONFIGURATIONS ---
MAX_PARTY_SIZE = 12
OPENING_HOUR = 11  # 11:00 AM
CLOSING_HOUR = 23  # 11:00 PM
MANAGER_CONTACT = "9916437369"
RESTAURANT_TIMEZONE = os.environ.get("RESTAURANT_TIMEZONE", "Asia/Kolkata")


def restaurant_now():
    return datetime.now(ZoneInfo(RESTAURANT_TIMEZONE))


def add_one_month(d):
    month = d.month + 1
    year = d.year
    if month == 13:
        month = 1
        year += 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def clean_param(value):
    if value is None:
        return None
    value = str(value).strip()
    # Remove common sentence punctuation that users include after IDs/times.
    return value.strip(" .,;")


def is_invalid_planner_value(value):
    if value is None:
        return True
    text = str(value).strip().lower()
    return (
        text == ""
        or text == "none"
        or text == "null"
        or "user__askuser" in text
        or "askuser" in text
        or "question=" in text
        or "please provide" in text
        or "how many people" in text
    )


def validate_required_fields(*fields):
    if any(is_invalid_planner_value(value) for value in fields):
        return False, "Reservation failed. Missing required booking details."
    return True, "Valid"


def is_invalid_customer_name(value):
    if is_invalid_planner_value(value):
        return True
    text = str(value).strip()
    normalized = re.sub(r"\s+", " ", text).lower()
    placeholder_names = {
        "user", "customer", "guest", "john doe", "jane doe", "test", "name",
        "unknown", "none", "null", "na", "n/a", "anonymous"
    }
    if normalized in placeholder_names:
        return True
    letters_only = re.sub(r"[^a-z]", "", normalized)
    if len(letters_only) < 2:
        return True
    if len(set(letters_only)) == 1 and len(letters_only) >= 3:
        return True
    if re.fullmatch(r"[a-z]", normalized):
        return True
    return False


def validate_customer_name(value):
    if is_invalid_customer_name(value):
        return False, "Reservation failed. Please provide a real customer name for the booking."
    return True, "Valid"


def compact_text(value, max_len=500):
    if is_invalid_planner_value(value):
        return None
    return str(value).strip()[:max_len]


def parse_update_request(update_type, new_value, update_details):
    """Map Bedrock's compact 5-parameter update schema to concrete update fields."""
    new_date = None
    new_time = None
    party_size = None
    new_customer_name = None
    lookup_customer_name = None
    special_requests = None

    def assign(kind, value):
        nonlocal new_date, new_time, party_size, new_customer_name, lookup_customer_name, special_requests
        if not value:
            return
        kind = str(kind).strip().lower()
        value = clean_param(value)
        if kind in ("date", "newdate", "bookingdate"):
            new_date = value
        elif kind in ("time", "newtime", "bookingtime"):
            new_time = value
        elif kind in ("partysize", "party_size", "party", "guests", "size"):
            party_size = value
        elif kind in ("name", "customername", "customer_name"):
            new_customer_name = value
        elif kind in ("lookupname", "customerlookupname", "lookup_customer_name"):
            lookup_customer_name = value
        elif kind in ("specialrequests", "special_requests", "accessibility", "seating", "request", "requests"):
            special_requests = value

    assign(update_type, new_value)

    if update_details:
        details = str(update_details).strip()
        try:
            parsed = json.loads(details)
            if isinstance(parsed, dict):
                for key, value in parsed.items():
                    assign(key, value)
        except Exception:
            lowered = details.lower()
            time_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", details)
            date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", details)
            party_match = re.search(r"\bparty\s*(?:size)?\s*(?:to|=|is)?\s*(\d{1,2})\b", lowered)
            lookup_match = re.search(r"(?:lookup|find|under|name)\s+([a-z][a-z .'-]{1,60})", lowered)
            name_change_match = re.search(r"(?:change\s+name\s+to|name\s+to)\s+([a-z][a-z .'-]{1,60})", lowered)

            if time_match:
                new_time = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
            if date_match:
                new_date = date_match.group(1)
            if party_match:
                party_size = party_match.group(1)
            if lookup_match:
                candidate = lookup_match.group(1).strip(" .,'-\"")
                if candidate:
                    lookup_customer_name = candidate
            if name_change_match:
                candidate = name_change_match.group(1).strip(" .,'-\"")
                if candidate:
                    new_customer_name = candidate

    return new_date, new_time, party_size, new_customer_name, lookup_customer_name, special_requests

def validate_reservation(booking_date, booking_time, party_size):
    """Validates restaurant policies before executing database transactions."""
    has_fields, missing_msg = validate_required_fields(booking_date, booking_time, party_size)
    if not has_fields:
        return False, missing_msg

    # 1. Party Size Validation
    try:
        size = int(party_size)
        if size > MAX_PARTY_SIZE:
            return False, f"ESCALATE_LARGE_PARTY: Party size of {size} exceeds standard capacity limits."
        if size <= 0:
            return False, "Reservation failed. Party size must be at least 1 guest."
    except (ValueError, TypeError):
        return False, "Reservation failed. Invalid party size parameter format provided."

    # 2. Operating Hours Validation
    try:
        time_obj = datetime.strptime(booking_time, "%H:%M").time()
        if not (OPENING_HOUR <= time_obj.hour < CLOSING_HOUR):
            return False, f"Reservation failed. R-Cafe operates strictly between {OPENING_HOUR}:00 and {CLOSING_HOUR}:00."
    except (ValueError, TypeError):
        return False, "Reservation failed. Invalid booking time format. Please use HH:MM."

    # 3. Date, Past Time, and Booking Window Validation
    try:
        booking_dt = datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
        booking_dt = booking_dt.replace(tzinfo=ZoneInfo(RESTAURANT_TIMEZONE))
        now = restaurant_now()
        if booking_dt < now:
            return False, "Reservation failed. You cannot schedule a table reservation in the past."

        max_booking_date = add_one_month(now.date())
        if booking_dt.date() > max_booking_date:
            return False, f"Reservation failed. R-Cafe accepts reservations only up to {max_booking_date.isoformat()}."
    except (ValueError, TypeError):
        return False, "Reservation failed. Invalid date/time structural pattern supplied."

    return True, "Valid"


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table("Restro-Table_booking-R-Cafe")

    action_group = event.get('actionGroup')
    function_name = event.get('function')

    # Safely unpack flat parameters array passed from Bedrock Agents
    params = {}
    for p in event.get('parameters', []):
        params[p.get('name')] = clean_param(p.get('value'))

    response_body = "Function routing execution failed"

    try:
        if function_name == 'createbooking':
            booking_date = params.get('booking_date')
            booking_time = params.get('booking_time')
            customer_name = params.get('customer_name')
            party_size = params.get('party_size')
            special_requests = compact_text(params.get('specialRequests') or params.get('special_requests'))

            has_fields, missing_msg = validate_required_fields(customer_name, booking_date, booking_time, party_size)
            has_name, name_msg = validate_customer_name(customer_name)
            if not has_fields:
                response_body = missing_msg
            elif not has_name:
                response_body = name_msg
            else:
                # Policy barrier checks
                is_valid, validation_msg = validate_reservation(booking_date, booking_time, party_size)
                if not is_valid:
                    if "ESCALATE_LARGE_PARTY" in validation_msg:
                        print(f"ALERT: Large party reservation escalation initiated for {customer_name} (Party size: {party_size}).")
                        response_body = (
                            f"ESCALATE_LARGE_PARTY_TICKET: A party size of {party_size} requires human manager approval. "
                            f"Do not create an automatic booking. The customer can call or WhatsApp the R-Cafe manager at {MANAGER_CONTACT}, "
                            f"or provide a valid Indian callback mobile number for future manager follow-up. "
                            f"Manager review SLA is 5 minutes in the future workflow; ticketing and callbacks are not active yet."
                        )
                    else:
                        response_body = validation_msg
                else:
                    booking_id = f"R-{str(uuid.uuid4())[:6].upper()}"
                    booking_date_time = f"{booking_date} {booking_time}"

                    item = {
                        'Booking_ID': booking_id,
                        'Booking_DateTime': booking_date_time,
                        'customer_name': customer_name,
                        'party_size': int(party_size)
                    }
                    if special_requests:
                        item['special_requests'] = special_requests
                    # Prevent silent primary composite key overwrites
                    table.put_item(
                        Item=item,
                        ConditionExpression="attribute_not_exists(Booking_ID) AND attribute_not_exists(Booking_DateTime)"
                    )
                    response_body = f"Success! Table booked for {customer_name} for a party of {party_size} on {booking_date} at {booking_time}. Your unique Booking ID is {booking_id}."

        elif function_name == 'getBooking':
            booking_id = params.get('bookingId')
            booking_date = params.get('bookingDate')
            booking_time = params.get('bookingTime')
            has_fields, missing_msg = validate_required_fields(booking_id, booking_date, booking_time)
            if not has_fields:
                response_body = missing_msg
            else:
                booking_date_time = f"{booking_date} {booking_time}"

                response = table.get_item(Key={'Booking_ID': booking_id, 'Booking_DateTime': booking_date_time})
                if 'Item' in response:
                    res = response['Item']
                    response_body = f"Found reservation details: Booking ID {res['Booking_ID']} for {res['customer_name']}, party size of {res['party_size']} on date and time {res['Booking_DateTime']}."
                else:
                    response_body = f"No reservation details found matching Booking ID {booking_id} at {booking_date_time}."

        elif function_name == 'updateBooking':
            booking_id = params.get('bookingId')
            booking_date = params.get('bookingDate')
            booking_time = params.get('bookingTime')
            new_date = params.get('newDate')
            new_time = params.get('newTime')
            party_size = params.get('partySize')
            customer_name = params.get('customerName')
            lookup_customer_name = params.get('customerLookupName') or params.get('lookupCustomerName')

            parsed_date, parsed_time, parsed_size, parsed_name, parsed_lookup_name, parsed_special_requests = parse_update_request(
                params.get('updateType'),
                params.get('newValue'),
                params.get('updateDetails') or params.get('newValue')
            )
            new_date = new_date or parsed_date
            new_time = new_time or parsed_time
            party_size = party_size or parsed_size
            customer_name = customer_name or parsed_name
            lookup_customer_name = lookup_customer_name or parsed_lookup_name
            special_requests = compact_text(params.get('specialRequests') or params.get('special_requests') or parsed_special_requests)

            # If the agent sends customerName while the booking ID is missing, treat it as a lookup name,
            # not as a requested name change. This handles: "I forgot the ID, check my name Raj".
            if not booking_id and not lookup_customer_name and customer_name:
                lookup_customer_name = customer_name
                customer_name = None

            if not any([new_date, new_time, party_size, customer_name, special_requests]):
                response_body = "Update failed. Please provide a new name, new date, new time, new party size, or special request details."
            else:
                current_date_time = f"{booking_date} {booking_time}" if booking_date and booking_time else None
                old_item = None

                if booking_id and current_date_time:
                    old_res = table.get_item(Key={'Booking_ID': booking_id, 'Booking_DateTime': current_date_time})
                    old_item = old_res.get('Item')
                elif lookup_customer_name:
                    if current_date_time:
                        lookup_res = table.query(
                            IndexName='r-cafe-index',
                            KeyConditionExpression=Key('customer_name').eq(lookup_customer_name) & Key('Booking_DateTime').eq(current_date_time)
                        )
                    else:
                        lookup_res = table.query(
                            IndexName='r-cafe-index',
                            KeyConditionExpression=Key('customer_name').eq(lookup_customer_name)
                        )
                    matches = lookup_res.get('Items', [])
                    if len(matches) == 1:
                        old_item = matches[0]
                        booking_id = old_item['Booking_ID']
                        current_date_time = old_item['Booking_DateTime']
                    elif len(matches) > 1:
                        match_list = [f"ID: {i['Booking_ID']} on {i['Booking_DateTime']}" for i in matches]
                        response_body = "Multiple bookings found. Please choose which booking to update: " + ", ".join(match_list)
                    else:
                        response_body = f"No reservation found under name {lookup_customer_name}."
                elif booking_id:
                    lookup_res = table.query(KeyConditionExpression=Key('Booking_ID').eq(booking_id))
                    matches = lookup_res.get('Items', [])
                    if len(matches) == 1:
                        old_item = matches[0]
                        current_date_time = old_item['Booking_DateTime']
                    elif len(matches) > 1:
                        match_list = [f"ID: {i['Booking_ID']} on {i['Booking_DateTime']}" for i in matches]
                        response_body = "Multiple bookings found for that ID. Please provide the current date and time: " + ", ".join(match_list)
                    else:
                        response_body = f"No reservation details found matching Booking ID {booking_id}."
                else:
                    response_body = "Update failed. Please provide a Booking ID or customer name to locate the reservation."

                if old_item:
                    booking_id = old_item['Booking_ID']
                    old_date, old_time = current_date_time.split(" ")
                    final_date = new_date if new_date else old_date
                    final_time = new_time if new_time else old_time
                    final_size = party_size if party_size else old_item.get('party_size')
                    final_customer_name = customer_name if customer_name else old_item.get('customer_name')
                    has_name, name_msg = validate_customer_name(final_customer_name)

                    is_valid, validation_msg = validate_reservation(final_date, final_time, final_size)
                    if not has_name:
                        response_body = name_msg
                    elif not is_valid:
                        if "ESCALATE_LARGE_PARTY" in validation_msg:
                            response_body = (
                                f"ESCALATE_LARGE_PARTY_TICKET: Upgrading party size to {final_size} requires human manager approval. "
                                f"The customer can call or WhatsApp the R-Cafe manager at {MANAGER_CONTACT}, "
                                f"or provide a valid Indian callback mobile number for future manager follow-up. "
                                f"Manager review SLA is 5 minutes in the future workflow; ticketing and callbacks are not active yet."
                            )
                        else:
                            response_body = validation_msg
                    else:
                        new_date_time = f"{final_date} {final_time}"
                        if new_date_time != current_date_time:
                            new_item = {
                                'Booking_ID': booking_id,
                                'Booking_DateTime': new_date_time,
                                'customer_name': final_customer_name,
                                'party_size': int(final_size)
                            }
                            if special_requests:
                                new_item['special_requests'] = special_requests
                            elif old_item.get('special_requests'):
                                new_item['special_requests'] = old_item.get('special_requests')
                            table.put_item(
                                Item=new_item,
                                ConditionExpression="attribute_not_exists(Booking_ID) AND attribute_not_exists(Booking_DateTime)"
                            )
                            table.delete_item(Key={'Booking_ID': booking_id, 'Booking_DateTime': current_date_time})
                        else:
                            update_expr = "SET party_size = :p, customer_name = :c"
                            expr_values = {':p': int(final_size), ':c': final_customer_name}
                            if special_requests:
                                update_expr += ", special_requests = :s"
                                expr_values[':s'] = special_requests
                            table.update_item(
                                Key={'Booking_ID': booking_id, 'Booking_DateTime': current_date_time},
                                UpdateExpression=update_expr,
                                ExpressionAttributeValues=expr_values
                            )
                        response_body = f"Successfully updated booking {booking_id}. New reservation details: {new_date_time} for {final_customer_name} with party size {final_size}."

        elif function_name == 'deleteBooking':
            booking_id = params.get('bookingId')
            booking_date = params.get('bookingDate')
            booking_time = params.get('bookingTime')
            has_fields, missing_msg = validate_required_fields(booking_id, booking_date, booking_time)
            if not has_fields:
                response_body = missing_msg
            else:
                booking_date_time = f"{booking_date} {booking_time}"
                table.delete_item(Key={'Booking_ID': booking_id, 'Booking_DateTime': booking_date_time})
                response_body = f"Reservation {booking_id} on {booking_date_time} has been completely removed."

        elif function_name == 'findBookingByName':
            customer_name = params.get('customerName')
            has_fields, missing_msg = validate_required_fields(customer_name)
            if not has_fields:
                response_body = "Reservation lookup failed. Customer name is required."
            else:
                # Using your newly added console index name
                response = table.query(
                    IndexName='r-cafe-index',
                    KeyConditionExpression=Key('customer_name').eq(customer_name)
                )
                items = response.get('Items', [])
                if not items:
                    response_body = f"No reservation strings found under name: {customer_name}"
                else:
                    matches = [f"ID: {i['Booking_ID']} on {i['Booking_DateTime']}" for i in items]
                    response_body = f"Found the following bookings for {customer_name}: " + ", ".join(matches)

        else:
            response_body = f"Unknown action: {function_name}"

    except Exception as e:
        print(f"Exception triggered in handler: {str(e)}")
        response_body = f"Error processing database transaction: {str(e)}"

    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'function': function_name,
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': response_body
                    }
                }
            }
        }
    }
