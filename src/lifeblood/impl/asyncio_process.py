from asyncio import streams, subprocess, create_task
from lifeblood.process_container import ProcessBase, ProcessContainerBase
from lifeblood.process_utils import kill_process_tree


class AsyncioProcess(ProcessBase):
    def __init__(self, container: ProcessContainerBase, process: subprocess.Process):
        self.__container = container
        self.__process = process
        self.__kill_task = None

    def container(self) -> ProcessContainerBase:
        return self.__container

    def stdin(self) -> streams.StreamWriter | None:
        return self.__process.stdin

    def stdout(self) -> streams.StreamReader | None:
        return self.__process.stdout

    def stderr(self) -> streams.StreamReader | None:
        return self.__process.stderr

    async def wait(self) -> int:
        ret = await self.__process.wait()
        if self.__kill_task:
            await self.__kill_task

        self.__process._transport.close()  # sometimes not closed straight away transport ON EXIT may cause exceptions in __del__ that event loop is closed
        return ret

    def return_code(self) -> int | None:
        return self.__process.returncode

    def kill(self):
        if self.__kill_task is not None:
            return
        self.__kill_task = create_task(self.__kill())

    async def __kill(self):
        await kill_process_tree(self.__process)

