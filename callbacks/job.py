import telegram
from telegram.ext import JobQueue

import datetime
import random
import time

from models.storage import MongoService
from utils.create_time import create_time
from models.job import Job
from models.job_mode import JobMode


storage = MongoService.get_instsance()

# def change_standup_job_schedule(
#         job_queue: JobQueue, time_str: str, hour: int, minute: int,
# ):
#     job_queue.stop()

#     jobs = job_queue.jobs()
#     for job in jobs:
#         job.schedule_removal()

#     DB().set_standup_time(time_str)

#     job_queue.run_daily(
#         callback=standup_job_handler_callback,
#         time=datetime.time(hour=hour, minute=minute),
#         days=(0, 2, 3, 4),
#     )
#     job_queue.start()
#     Logger().clear()


def add_notify_event(job_queue: JobQueue, job_model: Job):
    job_name = str(job_model.chat_id) + '_' + job_model.name

    if job_model.mode == JobMode.ONCE:
        job_queue.run_once(
            callback=notify_callback,
            name=job_name,
            when=create_time(job_model.time),
        )
    elif job_model.mode == JobMode.DAILY:
        job_queue.run_daily(
            callback=notify_callback,
            name=job_name,
            time=create_time(job_model.time),
            days=(0, 2, 3, 4),  # Monday-Friday
        )


def notify_callback(bot: telegram.Bot, job: telegram.ext.Job):
    chat_id, name = job.name.split('_', 1)
    chat_id = int(chat_id)

    job_model: Job = MongoService.get_instsance().find_unique_job(
        chat_id=chat_id, name=name,
    )

    shuffled_members = job_model.notify_users
    random.shuffle(shuffled_members)
    notify_users_str = ' '.join(shuffled_members)

    description = job_model.description
    event_name = job_model.name

    call_text = (
        notify_users_str
        + '\n\n'
        + 'Мероприятие: '
        + event_name
        + '\n\n'
        + description
    )

    if job_model.mode == JobMode.ONCE:
        storage.delete_one(chat_id=chat_id, name=name)

    bot.send_message(chat_id=chat_id, text=call_text)
