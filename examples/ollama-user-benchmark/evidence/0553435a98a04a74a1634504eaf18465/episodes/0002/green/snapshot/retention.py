def expired(age_days, retention_days):
    if age_days < 0 or retention_days < 0:
        raise ValueError("Age and retention must be non-negative integers.")
    return age_days >= retention_days
