import asyncio

from app.database import create_schema
from app.worker import run_forever


async def main() -> None:
    await create_schema()
    await run_forever()


if __name__ == "__main__":
    asyncio.run(main())

