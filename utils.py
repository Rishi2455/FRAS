"""
Utility functions for the attendance system.
"""
import datetime

def get_current_datetime():
    """Get the current date and time."""
    return datetime.datetime.now()

def format_date(date_obj):
    """Format a date object to YYYY-MM-DD string."""
    return date_obj.strftime("%Y-%m-%d")

def format_time(date_obj):
    """Format a date object to HH:MM:SS string."""
    return date_obj.strftime("%H:%M:%S")

def parse_date(date_string):
    """Parse a date string in YYYY-MM-DD format."""
    return datetime.datetime.strptime(date_string, "%Y-%m-%d")

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
