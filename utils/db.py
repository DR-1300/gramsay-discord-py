import aiomysql
import os

class Database:
    def __init__(self, pool):
        self.pool = pool
