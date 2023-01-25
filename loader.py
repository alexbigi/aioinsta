from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from requests_futures.sessions import FuturesSession

import config
from models.FastBotInst import FastBotInst

bot = FastBotInst(config.TOKEN)

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///aps_scheduler_jobs.sqlite')
}
Scheduler = AsyncIOScheduler(jobstores=jobstores)

app = FastAPI(title='FASToINST', description='Framework for instagram message api', version='0.1alfa',
              docs_url=None, redoc_url=None)

