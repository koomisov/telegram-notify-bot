import typing as tp

from pymongo import MongoClient

from models.job import Job
from models.job import parse


class MongoService(object):
    _instance = None
    _client = None
    _db = None

    @classmethod
    def get_instsance(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls.__init__(cls._instance, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._client = MongoClient('mongodb', 27017)
        self._db = self._client.telegram_bot_db

    def get_all(self) -> tp.List[Job]:
        """
            doc example:
                {
                    "chat_id": 123182384,
                    "description": "https://yandex.zoom.us/",
                    "notify_users": ["@bless_rng_322", "@vasya_pupkin"],
                    "name": "standup",
                    "mode": "once",
                    "time": "09:15"
                }
        """
        print(list(self._db.jobs.find({})))
        return [
            parse(job_raw=job_raw) for job_raw in list(self._db.jobs.find())
        ]

    def job_exists(self, chat_id: int, name: str) -> bool:
        job = self.find_unique_job(chat_id=chat_id, name=name)
        return job is not None

    def delete_one(self, chat_id: int, name: str) -> None:
        self._db.jobs.delete_one({'chat_id': chat_id, 'name': name})

    def find_unique_job(self, chat_id: int, name: str) -> tp.Optional[Job]:
        job_raw = self._db.jobs.find_one({'chat_id': chat_id, 'name': name})
        if not job_raw:
            return None

        return parse(job_raw=job_raw)

    def find_by_chat_id(self, chat_id: int) -> tp.List[Job]:
        jobs_raw = self._db.jobs.find({'chat_id': chat_id})
        return [parse(job_raw=job_raw) for job_raw in list(jobs_raw)]

    def insert_one(self, job_model: Job):
        return self._db.jobs.insert_one(
            {
                'chat_id': job_model.chat_id,
                'name': job_model.name,
                'description': job_model.description,
                'notify_users': job_model.notify_users,
                'mode': job_model.mode.value,
                'time': job_model.time,
            },
        )
