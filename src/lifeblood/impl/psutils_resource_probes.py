import asyncio

import psutil
from psutil import cpu_percent

from lifeblood.process_container import ProcessContainerBase
from lifeblood.resource_probe import ResourceProbeBase, ResourceProbeFactoryBase
from lifeblood.worker_resource_definition import WorkerResourceDefinition, WorkerResourceDataType


class PsutilsResourceProbe(ResourceProbeBase):
    _cpu_def = WorkerResourceDefinition(
        'cpu_load',
        WorkerResourceDataType.GENERIC_FLOAT,
        'cpu load',
        'cpu load',
        0.0,
    )
    _mem_def = WorkerResourceDefinition(
        'cpu_mem',
        WorkerResourceDataType.MEMORY_BYTES,
        'cpu RAM usage',
        'cpu RAM',
        0,
    )

    def probed_definitions(self) -> set[WorkerResourceDefinition]:
        return {
            self._cpu_def,
            self._mem_def,
        }

    async def probe(self, container: ProcessContainerBase, resource_subset: set[WorkerResourceDefinition] | None) -> dict[WorkerResourceDefinition, int | float]:
        result = {}
        if resource_subset is None or self._cpu_def in resource_subset:
            # cpu_percent measures load between two calls,
            #  so we do this trick
            psutil.cpu_percent()
            await asyncio.sleep(1.0)
            result[self._cpu_def] = psutil.cpu_percent()
        if resource_subset is None or self._mem_def in resource_subset:
            result[self._mem_def] = psutil.virtual_memory().used
        return result


class PsutilsResourceProbeFactory(ResourceProbeFactoryBase):
    async def create_probe(self) -> ResourceProbeBase:
        return PsutilsResourceProbe()
