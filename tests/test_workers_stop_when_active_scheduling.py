import aiosqlite
import asyncio
from contextlib import contextmanager
from pathlib import Path

from lifeblood.basenode_serializer_v2 import NodeSerializerV2
from lifeblood.net_messages.address import DirectAddress
from lifeblood.pluginloader import PluginNodeDataProvider
from lifeblood.simple_worker_pool import SimpleWorkerPool
from lifeblood.worker_pool_message_processor import WorkerPoolMessageProcessor
from lifeblood_testing_common.integration_common import IsolatedAsyncioTestCaseWithDb
from lifeblood_testing_common.common import chain
from lifeblood_testing_common.scheduler_config_provider_default_override import SchedulerConfigProviderOverrides
from unittest import mock
import lifeblood
from lifeblood.enums import TaskState, WorkerState, WorkerPingState, TaskScheduleStatus, InvocationState
from lifeblood.invocationjob import InvocationJob, InvocationResources
from lifeblood.scheduler.data_access import DataAccess, TaskSpawnData
from lifeblood.scheduler.scheduler import Scheduler
from lifeblood.nethelpers import get_localhost
from lifeblood.taskspawn import NewTask

from typing import List, Optional


async def get_invocation_resources_assigned_to_mock(*args, **kwargs) -> InvocationResources:
    return InvocationResources({}, {})


_orig_method = lifeblood.scheduler.data_access.DataAccess.get_invocation_resources_assigned_to

async def mock_get_invocation_resources_assigned_to(self, worker_id: int) -> Optional[InvocationResources]:
    await asyncio.sleep(0.1)
    return await _orig_method(self, worker_id)


class WorkersStopWhenActiveScheduling(IsolatedAsyncioTestCaseWithDb):
    """
    Test tries to catch any possible race happening between two main transactions
    in scheduling and worker stopping
    """
    async def test_workers_stop(self):
        await self._helper_test_workers_stop(
            worker_count=10,
            arbitrary_delay=1.0,
            tasks_to_spawn=100,
        )

    @mock.patch('lifeblood.scheduler.data_access.DataAccess.get_invocation_resources_assigned_to', mock_get_invocation_resources_assigned_to)
    async def _helper_test_workers_stop(self, tasks_to_spawn: int = 100, worker_count: int = 10, arbitrary_delay: float = 1.0):
        print('starting scheduler')
        config = SchedulerConfigProviderOverrides(self.db_file, 60, do_broadcast=False)
        sched = Scheduler(
            scheduler_config_provider=config,
            node_data_provider=PluginNodeDataProvider(  # TODO: make a test provider that only provides certain types
                plugin_paths=(
                    (Path(lifeblood.__file__).parent / 'core_nodes', 'core'),
                )
            ),
            node_serializers=[NodeSerializerV2()],
        )
        await sched.start()

        # init tasks
        print('initializing nodes')
        node_id = await sched.add_node('python', 'test node')
        node = await sched._get_node_object_by_id(node_id)
        node.set_param_value('process', 'schedule()')
        node.set_param_value(
            'invoke',
            'import time\n'
            'time.sleep(0.4)\n'
        )
        print('initializing tasks')
        for i in range(tasks_to_spawn):
            await sched.spawn_tasks(NewTask(f'task {i}', node_id))

        # init workers
        print('initializing worker pool')
        worker_pool = SimpleWorkerPool(
            minimal_idle_to_ensure=worker_count,
            maximum_total=worker_count,
            scheduler_address=sched.server_message_address(DirectAddress(get_localhost())),
            message_processor_factory=WorkerPoolMessageProcessor,
        )
        await worker_pool.start()

        # wait for workers to get busy
        print('waiting bare minimum load')
        for _ in range(600):  # reasonably big, yet finite to fail if error
            working_worker_count = worker_pool.total_active_worker_count() - worker_pool.idle_active_worker_count()
            if working_worker_count > worker_count * 0.75:
                break
            await asyncio.sleep(0.5)

        # now wait arbitrary time, just cuz
        print(f'waiting arbitrary for {arbitrary_delay}s')
        await asyncio.sleep(arbitrary_delay)

        # now make all workers gracefully close, imitating machine shutdown
        print('stopping worker pool')
        worker_pool.stop()
        await worker_pool.wait_till_stops()

        # finish
        print('stopping scheduler')
        sched.stop()
        await sched.wait_till_stops()
        # we expect to not get any exceptions from cleaned up asyncio tasks here
