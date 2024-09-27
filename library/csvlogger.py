import asyncio
import csv
import io
import logging
import os
import aiofiles
from datetime import datetime
from typing import List
from .datatypes import Configuration, Consumer, NotifData


class CSVLogger(Consumer):
    def __init__(self, config: Configuration, halt_event: asyncio.Event, data_path=None, callback=None):
        super().__init__()
        self.log = logging.getLogger('log')
        self.config = config
        self.halt_event = halt_event
        self.callback = callback
        if data_path:
            self.data_path = data_path
        else:
            self.data_path = self.config.output_folder
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        self.file_outputs = {}
        self.tasks = []
        self.start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    async def on_new_data_recieved(next_data):
        # Your code here, e.g., logging, notifications, etc.
        pass

    async def run(self, callback = None):

        try:
            while not self.halt_event.is_set() or not self.input_queue.empty():
                try:
                    next_data = await asyncio.wait_for(
                        self.input_queue.get(), timeout=0.5
                    )  # type: NotifData
                    self.new_data = next_data
                    await self._log_to_file(next_data)
                except asyncio.TimeoutError:
                    pass

        except Exception as e:
            self.log.error(f"CSVLogger encountered an exception: {e}")
            self.halt_event.set()
        finally:
            total_output_q = sum(
                [c.input_queue.qsize() for c in self.file_outputs.values()]
            )
            if total_output_q > 0:
                self.log.info(f"CSVLogger ready to shut down. Waiting for {total_output_q} items in output queues...")
            try:
                await asyncio.gather(*self.tasks)
            except asyncio.CancelledError:
                pass
            self.log.info("CSVLogger shut down")

    async def _log_to_file(self, next_data: NotifData):
        # determine file path:
        file_path = self.file_path(next_data.device_adr, next_data.characteristic)

        if file_path not in self.file_outputs:
            # File not yet opened, open:
            file_output = FileWriter(file_path, next_data.characteristic.column_headers, self.halt_event)
            self.file_outputs[file_path] = file_output
            file_task = asyncio.create_task(self.file_outputs[file_path].run(), name='File Task')
            self.tasks.append(file_task)

        if self.file_outputs[file_path].active:
            # Open, write:
            await self.file_outputs[file_path].input_queue.put(next_data)

    def file_path(self, device_adr, char):
        if device_adr in self.config.device_aliases:
            name = self.config.device_aliases[device_adr]
        else:
            name = device_adr.replace(":", "_")

        n = f"{name}_{self.start_time}_{char.name}.csv"
        n = n.replace(" ", "_")

        if self.data_path == None:
            return os.path.join(self.config.output_folder, n)
        else:
            return os.path.join(self.data_path, n)


class FileWriter:
    def __init__(self, file_path: str, column_headers: List[str], halt_event: asyncio.Event):
        self.file_path = file_path
        self.column_headers = column_headers
        self.halt_event = halt_event
        self.log = logging.getLogger('log')
        self.input_queue = asyncio.Queue()
        self.active = True

    async def run(self):
        f = None

        try:
            if os.path.exists(self.file_path):
                f = await aiofiles.open(self.file_path, "a", newline="")
                # self.log.info(f'Opened {self.file_path}')
            else:
                f = await aiofiles.open(self.file_path, "w", newline="")
                await self.write_row(f, self.column_headers)
                # self.log.info(f'Created {self.file_path}')

            while not (self.halt_event.is_set() and self.input_queue.empty()):
                try:
                    next_data = await asyncio.wait_for(
                        self.input_queue.get(), timeout=0.5
                    )  # type: NotifData
                    for row in next_data.data:
                        await self.write_row(f, row)
                    await f.flush()
                    self.input_queue.task_done()
                except asyncio.TimeoutError:
                    pass
        except FileNotFoundError as e:
            self.log.error(f"CSVLogger {self.file_path} encountered an exception: {e}")
        except Exception as e:
            self.log.error(f"CSVLogger {self.file_path} encountered an exception: {e}")
            self.halt_event.set()
        finally:
            self.active = False
            if f is not None:
                await f.close()

    async def write_row(self, f, row):
        row_str_io = io.StringIO()
        csv_writer = csv.writer(row_str_io)
        csv_writer.writerow(row)
        await f.write(row_str_io.getvalue())