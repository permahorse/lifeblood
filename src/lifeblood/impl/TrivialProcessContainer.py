import asyncio
from pathlib import Path
from lifeblood.process_container import ProcessBase, ProcessContainerBase
from lifeblood.invocationjob import Environment


class TrivialProcessContainer(ProcessContainerBase):
    def __init__(self):
        super().__init__()
        self.__processes: list[ProcessBase] = []
        self.__started = asyncio.Event()
        self.__destroyed = asyncio.Event()
        self.__kill_tasks = []

    async def create_process(self, args: list[str], *,
                       env: Environment,
                       cwd: str | Path | None,
                       ) -> ProcessBase:
        if self.__destroyed.is_set():
            raise RuntimeError('container already destroyed or is being destroyed')
        proc = await self._inner_create_process(args, env=env, cwd=cwd)
        self.__processes.append(proc)
        return proc

    async def _inner_create_process(self, args: list[str], *,
                       env: Environment,
                       cwd: str | Path | None,
                       ) -> ProcessBase:
        raise NotImplementedError()

    def destroy(self):
        self.__destroyed.set()
        processes = [p for p in self.__processes if p.is_running()]
        for proc in processes:
            proc.kill()

    async def wait(self):
        await self.__destroyed.wait()

        if self.__processes:
            await asyncio.gather(x.wait() for x in self.__processes)
