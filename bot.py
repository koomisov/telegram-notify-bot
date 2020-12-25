# -*- coding: utf-8 -*-
import telegram
import requests

from callbacks import job as job_callbacks
from callbacks import message as message_callbacks
from models.storage import MongoService


storage = MongoService.get_instsance()


def _get_bot_token() -> str:
    with open('BOT_TG_TOKEN.txt') as token_file:
        return token_file.read().replace('\n', '').replace('\r', '')


def _init_jobs_on_startup(job_queue: telegram.ext.JobQueue, storage) -> None:
    jobs = storage.get_all()

    for job_model in jobs:
        job_callbacks.add_notify_event(
            job_queue=job_queue, job_model=job_model,
        )


def main():
    photo_name = 'котик'
    photo_url = f'https://yandex.ru/images/search?text={photo_name}&ncrnd=1587506362789-6466307030731739'
    full_page = requests.get(photo_url)
    print(full_page.content)

    updater = telegram.ext.Updater(_get_bot_token())

    job_queue = updater.dispatcher.job_queue
    _init_jobs_on_startup(job_queue, storage)
    job_queue.start()

    message_handler = telegram.ext.MessageHandler(
        filters=telegram.ext.Filters.all,
        callback=message_callbacks.message_callback,
        pass_job_queue=True,
    )

    updater.dispatcher.add_handler(handler=message_handler)
    updater.start_polling(poll_interval=3.0)
    updater.idle()


if __name__ == '__main__':
    main()
