import asyncio
import os

MAX_PARALLEL_TASKS = max(1, os.cpu_count())

processing_semaphore = asyncio.Semaphore(MAX_PARALLEL_TASKS)

scan_queue = asyncio.Queue()