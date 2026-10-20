from typing import Iterable

import asyncio
from pathlib import Path
from lifeblood.process_container import ProcessBase, ProcessContainerBase
from lifeblood.invocationjob import Environment, InvocationEnvironment


class TrivialProcessContainer(ProcessContainerBase):
    def __init__(self, base_environment: Environment):
        super().__init__()
        self.__processes: list[ProcessBase] = []
        self.__base_env = base_environment
        self.__started = asyncio.Event()
        self.__destroyed = asyncio.Event()
        self.__kill_tasks = []

    async def all_processes(self) -> Iterable[ProcessBase]:
        """
        trivial container does not properly implement this function, as it misses all children
        """
        return tuple(self.__processes)

    async def create_process(self, args: list[str], *,
                       env: Environment | InvocationEnvironment | None,
                       cwd: str | Path | None,
                       ) -> ProcessBase:
        if self.__destroyed.is_set():
            raise RuntimeError('container already destroyed or is being destroyed')
        final_env = Environment(self.__base_env)
        if env is not None:
            if isinstance(env, InvocationEnvironment):
                env = env.resolve(self.__base_env)
            final_env.update(env)
        assert isinstance(final_env, Environment)
        proc = await self._inner_create_process(args, env=final_env, cwd=cwd)
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
            await asyncio.gather(*(x.wait() for x in self.__processes))

    def root_processes(self) -> tuple[ProcessBase, ...]:
        return tuple(self.__processes)