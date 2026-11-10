# Review: reservation

reservation.fits(capacity, booked, requested) returns a bool. All inputs are nonnegative integers with booked <= capacity. An exact fill is permitted: booked + requested <= capacity. Reject requests exceeding capacity. Do not reject zero requested seats at full capacity.

Review the current source without modifying it. Evaluate criterion `inclusive_capacity`; report pass, fail or abstain with source-bound findings. All requirements above are binding; style preferences are not requirements.
