import asyncio

import psutil
import time
from lifeblood.impl.asyncio_process import AsyncioProcess
from lifeblood.process_container import ProcessContainerBase
from lifeblood.resource_probe import ResourceProbeBase, ResourceProbeFactoryBase, ContainerNotSupportedError
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
        processes: list[psutil.Process] = []
        for proc in await container.all_processes():
            if not isinstance(proc, AsyncioProcess):
                raise ContainerNotSupportedError('no pid - no probe')
            p = psutil.Process(proc.get_pid())
            processes.append(p)
            processes += await asyncio.get_event_loop().run_in_executor(None, p.children, True)
        return await asyncio.get_event_loop().run_in_executor(None, self._probe_noasync, processes, resource_subset)

    def _probe_noasync(self, processes: list[psutil.Process], resource_subset: set[WorkerResourceDefinition] | None):
        result = {}
        if resource_subset is None or self._cpu_def in resource_subset:
            # cpu_percent measures load between two calls,
            #  so we do this trick
            for proc in processes:
                proc.cpu_percent()
            psutil.cpu_percent()
            time.sleep(1.0)
            total_cpu = 0.0
            for proc in processes:
                total_cpu += proc.cpu_percent()
            result[self._cpu_def] = total_cpu
        if resource_subset is None or self._mem_def in resource_subset:
            total_mem = 0
            for proc in processes:
                total_mem += proc.memory_info().rss
            result[self._mem_def] = total_mem
        return result


class PsutilsResourceProbeFactory(ResourceProbeFactoryBase):
    async def create_probe(self) -> ResourceProbeBase:
        return PsutilsResourceProbe()
