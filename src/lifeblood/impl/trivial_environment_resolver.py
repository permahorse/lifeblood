import os
from lifeblood.invocationjob import Environment
from lifeblood.environment_resolver import BaseSimpleProcessSpawnEnvironmentResolver
from lifeblood.impl.trivial_asyncio_process_container import TrivialAsyncioProcessContainerFactory

from typing import Mapping


class TrivialEnvironmentResolver(BaseSimpleProcessSpawnEnvironmentResolver):
    """
    trivial environment wrapper does nothing
    """
    def __init__(self):
        super().__init__(
            TrivialAsyncioProcessContainerFactory(),
        )

    async def get_environment(self, arguments: Mapping) -> "Environment":
        env = Environment(os.environ)
        for key, value in arguments.items():
            env[key] = value
        return env