def billable_minutes(seconds):
    if seconds < 0:
        raise ValueError("Seconds must be non-negative")
    if seconds == 0:
        return 0
    # To round up to the nearest minute using integer arithmetic:
    # (seconds + 59) // 60
    return (seconds + 59) // 60
