import aiomysql
import os

class Database:
    def __init__(self, pool):
        self.pool = pool
    
    @classmethod
    async def create(cls):
        pool = await aiomysql.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            db=os.getenv("DB_NAME"),
            autocommit=True,
            minsize=1,
            maxsize=10,
        )
        db = cls(pool)
        return db
    
    async def execute(self, query:str, *args):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, args)
                return cur.lastrowid
    async def fetchone(self, query: str, *args):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, args)
                return await cur.fetchone()
 
    async def fetchall(self, query: str, *args):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(query, args)
                return await cur.fetchall()
 
    def close(self):
        self.pool.close()
