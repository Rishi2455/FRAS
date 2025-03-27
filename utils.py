"""
Utility functions for the attendance system.
"""
import datetime
import pytz

# Define Kolkata timezone
KOLKATA_TZ = pytz.timezone('Asia/Kolkata')

def get_current_datetime():
    """Get the current date and time in Kolkata timezone."""
    return datetime.datetime.now(KOLKATA_TZ)

def format_date(date_obj):
    """Format a date object to YYYY-MM-DD string."""
    # Convert to Kolkata timezone if the date has a timezone
    if date_obj.tzinfo is not None:
        date_obj = date_obj.astimezone(KOLKATA_TZ)
    return date_obj.strftime("%Y-%m-%d")

def format_time(date_obj):
    """Format a date object to HH:MM:SS string."""
    # Convert to Kolkata timezone if the date has a timezone
    if date_obj.tzinfo is not None:
        date_obj = date_obj.astimezone(KOLKATA_TZ)
    return date_obj.strftime("%H:%M:%S")

def parse_date(date_string):
    """Parse a date string in YYYY-MM-DD format and set to Kolkata timezone."""
    date_obj = datetime.datetime.strptime(date_string, "%Y-%m-%d")
    return KOLKATA_TZ.localize(date_obj)

def calculate_date_range(start_date_str, end_date_str):
    """Calculate a range of dates between start and end dates."""
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    
    date_range = []
    current_date = start_date
    
    while current_date <= end_date:
        date_range.append(format_date(current_date))
        current_date += datetime.timedelta(days=1)
    
    return date_range

def validate_student_id(student_id):
    """Validate student ID format."""
    # Student ID should be a numeric string
    return student_id.isdigit()

def localize_datetime(dt):
    """Convert a naive datetime object to Kolkata timezone."""
    if dt.tzinfo is None:
        return KOLKATA_TZ.localize(dt)
    return dt.astimezone(KOLKATA_TZ)
