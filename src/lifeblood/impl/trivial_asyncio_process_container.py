import asyncio
import sys
import os
import shutil
from pathlib import Path
from lifeblood import logging
from lifeblood.impl.asyncio_process import AsyncioProcess
from lifeblood.process_container import ProcessBase, ProcessContainerBase, ProcessContainerFactoryBase
from lifeblood.invocationjob import Environment, InvocationResources
from lifeblood.process_utils import create_process, kill_process_tree
from lifeblood.exceptions import ProcessInitializationError

from .trivial_process_container import TrivialProcessContainer


class TrivialAsyncioProcessContainerFactory(ProcessContainerFactoryBase):
    async def create_process_container(
            self,
            resources_restrictions: InvocationResources | None,
            base_environment: Environment,
    ) -> ProcessContainerBase:
        logger = logging.get_logger('Trivial Process Container Factory')
        if resources_restrictions is None:
            logger.info('no resource restriction requested')
        else:
            logger.info(
                'requested resources:\n' +
                '\n'.join(f'\t{rname}={repr(rval)}' for rname, rval in resources_restrictions.resources.items()) +
                '\nrequested devices:\n' +
                '\n'.join(f'\t{dev_type}:{repr(dev_names_list)}' for dev_type, dev_names_list in
                          resources_restrictions.devices.items()) +
                '\nbut standard environment resolver has no means of enforcing these limitations'
            )
        return TrivialAsyncioProcessContainer(base_environment)


class TrivialAsyncioProcessContainer(TrivialProcessContainer):
    def __init__(self, base_environment: Environment):
        super().__init__(base_environment)
        self.__destroyed = asyncio.Event()
        self.__kill_tasks = []

    async def _inner_create_process(self, args: list[str], *,
                       env: Environment,
                       cwd: str | Path | None,
                       ) -> ProcessBase:
        #
        # This introduces path to sys.executable if no python is found in PATH, yet `python` is first arg in call_args
        #
        # even though lifeblood worker runs with python interpreter - it does NOT expect
        #  python to be available in run environment. User might want to have multiple versions of packaged python.
        #  However, simple one user artist might not care, and would just want python code to work without any packages setup.
        #  So to simplify the life of smaller setup users, this hack was introduced.
        if args[0] in ('python', 'python.exe') and shutil.which(args[0], path=env.get('PATH', '')) is None:
            env.append('PATH', os.path.dirname(sys.executable))

        if os.path.isabs(args[0]):
            bin_path = args[0]
        else:
            bin_path = shutil.which(args[0], path=env.get('PATH', ''))
        if bin_path is None:
            raise ProcessInitializationError(f'"{args[0]}" was not found. Check environment resolver arguments and system setup')

        if cwd is None:
            cwd = os.path.dirname(bin_path)

        unwrapped_process = await create_process(args, env, str(cwd))
        proc = AsyncioProcess(self, unwrapped_process)
        return proc

    def destroy(self):
        if self.__destroyed.is_set():
            return
        processes = [p for p in self.root_processes() if p.is_running()]
        for proc in processes:
            assert isinstance(proc, AsyncioProcess)
            if not proc.is_running():
                continue
            self.__kill_tasks.append(asyncio.create_task(kill_process_tree(proc.get_wrapped_process())))
        self.__destroyed.set()

    async def wait(self):
        await self.__destroyed.wait()
        if self.__kill_tasks:
            await asyncio.wait(self.__kill_tasks)
