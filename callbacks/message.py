import telegram
import time
import random
import argparse
import shlex
import json
import os
import typing
import re
from tabulate import tabulate

from callbacks import job as job_callbacks
from models.storage import MongoService
from models.job import parse
from models.job import Job
from models.job_mode import JobMode
from utils import create_time

storage = MongoService.get_instsance()


class ArgumentParserError(Exception):
    pass


class ThrowingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)


def _parse_args(source_chat_id: int, text: str, on_create: bool):
    parser = ThrowingArgumentParser()
    parser.add_argument(
        '--name', dest='name', nargs='+', type=str, required=True,
    )
    parser.add_argument('--time', dest='time', type=str, required=on_create)
    parser.add_argument('--mode', dest='mode', type=str, required=on_create)
    parser.add_argument(
        '--description',
        dest='description',
        type=str,
        nargs='+',
        required=on_create,
    )
    parser.add_argument(
        '--notify-users',
        dest='notify_users',
        nargs='+',
        type=str,
        required=False,
    )

    # parse and skip command
    args = parser.parse_args(text.split()[1:])

    args.name = ' '.join(args.name)
    if args.description is not None:
        args.description = ' '.join(args.description)

    return parse(
        {
            'chat_id': source_chat_id,
            'name': args.name,
            'mode': args.mode or JobMode.ONCE,
            'description': args.description,
            'time': args.time or '12:00',
            'notify_users': args.notify_users or [],
        },
    )


def _help_reply(bot: telegram.Bot, source_char_id: int):
    text = 'Добавление события: \n'
    text += """
            ```
    add-event
        --name=<name>
        --time=<time>
        --mode=<mode>
        --description=<description>
        --notify-users=<user1 @user2 ...>
        ```
        \n"""

    text += 'Удаление события: \n'
    text += """
            ```
    remove-event
        --name=<name>
        ```
        \n"""

    text += 'Список актуальный событий: \n'
    text += """
            ```
        events-list
        ```
        \n"""

    bot.send_message(
        chat_id=source_char_id,
        text=text,
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


def _add_event(
        bot: telegram.Bot,
        source_chat_id: int,
        text: str,
        job_queue: telegram.ext.JobQueue,
) -> None:
    try:
        job_model = _parse_args(source_chat_id, text, on_create=True)
    except Exception as exc:
        print(f'failed to parse add event command arguments: {exc}')
        return

    if storage.job_exists(name=job_model.name, chat_id=job_model.chat_id):
        bot.send_message(
            chat_id=source_chat_id,
            text=f'Мероприятие {job_model.name} уже существует',
        )
    else:
        storage.insert_one(job_model=job_model)

        job_callbacks.add_notify_event(
            job_queue=job_queue, job_model=job_model,
        )

        bot.send_message(
            chat_id=source_chat_id,
            text=f'Мероприятие {job_model.name} было успешно добавлено',
        )


def _remove_event(
        bot: telegram.Bot,
        source_chat_id: int,
        text: str,
        job_queue: telegram.ext.JobQueue,
) -> None:
    try:
        job_model = _parse_args(source_chat_id, text, on_create=False)
    except Exception as exc:
        print(f'failed to parse remove event command arguments: {exc}')
        return

    jobs_to_remove = job_queue.get_jobs_by_name(
        name=str(job_model.chat_id) + '_' + job_model.name,
    )

    if not jobs_to_remove:
        bot.send_message(
            chat_id=source_chat_id,
            text=f'Мероприятие {job_model.name} не найдено',
        )
        return

    for job_to_remove in jobs_to_remove:
        job_to_remove.enabled = False
        job_to_remove.schedule_removal()

    storage.delete_one(chat_id=job_model.chat_id, name=job_model.name)
    bot.send_message(
        chat_id=source_chat_id,
        text=f'Мероприятие {job_model.name} было удалено',
    )


def _events_list(bot: telegram.Bot, source_chat_id: int) -> None:
    chat_events = storage.find_by_chat_id(source_chat_id)
    chat_events = [
        [event.name, event.time, event.mode.value] for event in chat_events
    ]

    text = '```\n'
    text += str(
        tabulate(
            chat_events,
            headers=['Название', 'Время', 'Тип'],
            tablefmt='fancy_grid',
        ),
    )
    text += '\n```'

    bot.send_message(
        chat_id=source_chat_id,
        text=text,
        parse_mode=telegram.ParseMode.MARKDOWN,
    )


def message_callback(
        bot: telegram.Bot,
        update: telegram.Update,
        job_queue: telegram.ext.JobQueue,
):
    source_chat_id = update.message.chat_id
    text = update.message.text if update.message.text else ''

    if text == '/help':
        _help_reply(bot, source_chat_id)
    elif text.startswith('add-event '):
        _add_event(
            bot=bot,
            source_chat_id=source_chat_id,
            text=text,
            job_queue=job_queue,
        )
    elif text.startswith('remove-event '):
        _remove_event(
            bot=bot,
            source_chat_id=source_chat_id,
            text=text,
            job_queue=job_queue,
        )
    elif text == 'events-list':
        _events_list(bot=bot, source_chat_id=source_chat_id)
