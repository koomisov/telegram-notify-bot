import dataclasses
import typing as tp

from models.job_mode import JobMode


@dataclasses.dataclass
class Job:
    chat_id: int
    name: str
    mode: JobMode
    description: tp.Optional[str]
    notify_users: tp.List[str]
    time: str


def parse(job_raw: dict) -> Job:
    mode = None
    if job_raw['mode'] == 'daily':
        mode = JobMode.DAILY
    elif job_raw['mode'] == 'once':
        mode = JobMode.ONCE

    raw_users = job_raw.get('notify_users', [])
    users = []
    for user in raw_users:
        if not user:
            continue
        elif user[0] != '@':
            users.append('@' + user)
        else:
            users.append(user)

    return Job(
        chat_id=job_raw['chat_id'],
        name=job_raw['name'],
        mode=mode,
        description=job_raw.get('description'),
        notify_users=users,
        time=job_raw['time'],
    )
