import random
import datetime

def generate_period(dt=None):
    if dt is None:
        dt = datetime.datetime.utcnow()
    date_str = dt.strftime("%Y%m%d")
    total_minutes = dt.hour * 60 + dt.minute
    return f"{date_str}1000{10001 + total_minutes}"

def generate_prediction():
    raw = random.choice(["BIG", "SMALL"])
    # Ulta (reverse)
    result = "SMALL" if raw == "BIG" else "BIG"
    if result == "BIG":
        numbers = f"{random.randint(5,9)} {random.randint(5,9)}"
    else:
        numbers = f"{random.randint(0,4)} {random.randint(0,4)}"
    return result, numbers