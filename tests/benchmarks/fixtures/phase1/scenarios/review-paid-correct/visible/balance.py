from policy import eligible


def total(rows):
    return sum(row["cents"] for row in rows if eligible(row))
