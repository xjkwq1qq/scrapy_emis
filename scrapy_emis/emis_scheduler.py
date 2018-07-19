# -*- coding:utf-8 -*-
import settings
import redis


class RedisManager(object):
    def __init__(self):
        self.redis_pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    def get_redis_connect(self):
        return redis.Redis(connection_pool=self.redis_pool)

    def emis_job(self):
        r = self.get_redis_connect()
        r.lpush('scrapy_emis:start_urls', 'https://intellinet.deloitte.com/Secure/Forms/LoadContentProvider.aspx?LinkId=21')
        #r.lpush('scrapy_emis:start_urls', 'https://www.emis.com/php/companies?pc=CN&cmpy=1732088')

redisManager = RedisManager()

if __name__ == "__main__":
    # redisManager.start_scheduler_toRedis()
    redisManager.emis_job()
