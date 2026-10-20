from __future__ import annotations
from pathlib import Path
from asyncio import streams
from typing import Iterable

from lifeblood.invocationjob import InvocationEnvironment, Environment, InvocationResources


class ContainerDestroyedError(RuntimeError):
    pass


class ProcessContainerFactoryBase:
    async def create_process_container(
            self,
            resources_restrictions: InvocationResources | None,
            base_environment: Environment,
            # TODO: mounts, capabilities, etc, but somehow platform-independent
    ) -> ProcessContainerBase:
        raise NotImplementedError()


class ProcessContainerBase:
    async def create_process(self, args: list[str], *,
                             env: Environment | InvocationEnvironment | None,
                             cwd: str | Path | None,
                             ) -> ProcessBase:
        raise NotImplementedError()

    def all_processes(self) -> Iterable[ProcessBase]:
        """
        Returns all processes ran in container that are processes created with create_process, or descendants of those
        If a container creates auxiliary helper processes - those should NOT be returned by this
        """
        raise NotImplementedError()

    def destroy(self):
        """
        initiate container's destruction.
        Further operations with container will raise ContainerDestroyedError
        multiple destroy calls are allowed
        """
        raise NotImplementedError()

    async def wait(self):
        """
        wait until container is destroyed
        """
        raise NotImplementedError()


class ProcessBase:
    def container(self) -> ProcessContainerBase:
        raise NotImplementedError()

    def stdin(self) -> streams.StreamWriter | None:
        raise NotImplementedError()

    def stdout(self) -> streams.StreamReader | None:
        raise NotImplementedError()

    def stderr(self) -> streams.StreamReader | None:
        raise NotImplementedError()

    def is_running(self) -> bool:
        return self.return_code() is None

    async def wait(self) -> int:
        raise NotImplementedError()

    def return_code(self) -> int | None:
        raise NotImplementedError()

    def kill(self):
        raise NotImplementedError()
