import time
import asyncio
import logging
from typing import List
from .datatypes import Configuration, Consumer


class ConsumerManager:
    def __init__(self, config: Configuration, halt_event: asyncio.Event) -> None:
        self.config = config
        self.halt_event = halt_event
        self.log = logging.getLogger('log')
        self.consumers = []  # type: List[Consumer]
        self.consumer_tasks = []
        self.input_queue = asyncio.Queue()

    def add_consumer(self, c: Consumer):
        self.consumers.append(c)

    async def run(self) -> None:
        try:
            # Spinup all consumers
            self._launch_consumers()
            # Continuously distribute data to consumers
            while not self.halt_event.is_set() or not self.input_queue.empty():
                await self._distribute_data()
                self._monitor_timeouts()
        except Exception as e:
            self.log.error(f'ConsumerManager encountered an exception: {e}')
            self.halt_event.set()
        finally:
            # Shutdown all consumers
            total_output_q = sum([c.input_queue.qsize() for c in self.consumers])
            if total_output_q > 0:
                self.log.info(f'ConsumerManager ready to shut down. Waiting for {total_output_q} items in output queues...')
            # Await for all consumer tasks to finish
            if self.consumer_tasks:
                await asyncio.gather(*self.consumer_tasks)
            self.consumer_tasks = []
            self.consumers = []
            self.log.info('ConsumerManager shut down')

    def _launch_consumers(self) -> None:
        for consumer in self.consumers:
            task = asyncio.create_task(consumer.run(), name=f'Consumer_{consumer.__class__.__name__}_Task')
            self.consumer_tasks.append(task)
            self.log.info(f'Consumer {consumer.__class__.__name__} enabled')

    async def _distribute_data(self):
        try:
            # Grab data, distribute to all consumers:
            next_data = await asyncio.wait_for(self.input_queue.get(), timeout=0.5)
            for consumer in self.consumers:
                try:
                    consumer.input_queue.put_nowait(next_data)
                except asyncio.QueueFull:
                    self.log.warning(f'Consumer {type(consumer).__name__} did not accept data!')
            self.input_queue.task_done()
        except asyncio.TimeoutError:
            pass

    def _monitor_timeouts(self):
        # Check if any consumers are lagging behind:
        warn_thsh = 300
        for consumer in self.consumers:
            if consumer.input_queue.qsize() > warn_thsh:
                self.log.warning(f'The input queue of consumer {type(consumer).__name__} has more than {consumer.input_queue.qsize()} items, consumers are lagging!')
                consumer.last_full_queue_warning = time.monotonic_ns()