from __future__ import annotations

from lifeblood.process_container import ProcessContainerBase
from lifeblood.worker_resource_definition import WorkerResourceDefinition, WorkerResourceValue


class ProbeInitializationError(RuntimeError):
    pass


class ContainerNotSupportedError(RuntimeError):
    pass


class ResourceProbeProviderBase:
    def get_all_probe_factories(self) -> tuple[ResourceProbeFactoryBase, ...]:
        raise NotImplementedError()


class ResourceProbeFactoryBase:
    async def create_probe(self) -> ResourceProbeBase:
        raise NotImplementedError()


class ResourceProbeBase:
    def probed_definitions(self) -> set[WorkerResourceDefinition]:
        raise NotImplementedError()

    async def probe(self, container: ProcessContainerBase, resource_subset: set[WorkerResourceDefinition] | None) -> dict[WorkerResourceDefinition, WorkerResourceValue]:
        raise NotImplementedError()
