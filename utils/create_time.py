import datetime


def create_time(time: str):
    hour, minute = time.split(':', 1)
    # add check
    return datetime.time(
        hour=int(hour),
        minute=int(minute),
        tzinfo=datetime.timezone(datetime.timedelta(hours=3)),  # Europe/Moscow
    )
