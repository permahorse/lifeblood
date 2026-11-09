"""
environment wrapper is an object that produces runtime environment for an invocation
taking into account invocation's requirements and worker's machine specifics

For example you might want to at least pass the version of software you want to use together with
your invocation job

Or a more complicated environment wrapper would take in a whole set of required packages from invocation job
and produce an environment fitting those requirements

As I see the it, a freelancer or a studio would implement one specific to them environment wrapper
for all workers, not several different wrappers
"""
from __future__ import annotations
import asyncio
from types import MappingProxyType

from lifeblood.process_container import ProcessContainerBase, ProcessContainerFactoryBase
from .attribute_serialization import serialize_attributes_core, deserialize_attributes_core
from .invocationjob import Environment, InvocationResources

from typing import Mapping, Optional


class ResolutionImpossibleError(RuntimeError):
    pass


class EnvironmentResolverProviderBase:
    def get_resolver(self, name: str) -> BaseEnvironmentResolver:
        raise NotImplementedError()


class EnvironmentResolverArguments:
    """
    this class objects specify requirements a task/invocation have for it's worker environment wrapper.
    """
    def __init__(self, resolver_name=None, arguments: Optional[Mapping] = None):
        """

        :param resolver_name: if None - treat as no arguments at all
        :param arguments:
        """
        if arguments is None:
            arguments = {}
        if resolver_name is None and len(arguments) > 0:
            raise ValueError('if name is None - no arguments are allowed')
        self.__resolver_name = resolver_name
        if arguments is not None:
            # validate args
            serialize_attributes_core(arguments)
        self.__args = arguments

    def name(self):
        return self.__resolver_name

    def set_name(self, name: str):
        self.__resolver_name = name

    def arguments(self):
        return MappingProxyType(self.__args)

    def add_argument(self, name: str, value):
        # validate value
        serialize_attributes_core(value)
        self.__args[name] = value

    def remove_argument(self, name: str):
        del self.__args[name]

    def serialize(self) -> bytes:
        return serialize_attributes_core({
            '_EnvironmentResolverArguments__resolver_name': self.__resolver_name,
            '_EnvironmentResolverArguments__args': self.__args,
        }).encode('utf-8')

    async def serialize_async(self):
        return await asyncio.get_running_loop().run_in_executor(None, self.serialize)

    @classmethod
    def deserialize(cls, data: bytes):
        wrp = EnvironmentResolverArguments(None)
        data_dict = deserialize_attributes_core(data.decode('utf-8'))
        wrp.__resolver_name = data_dict['_EnvironmentResolverArguments__resolver_name']
        wrp.__args = data_dict['_EnvironmentResolverArguments__args']
        return wrp

    @classmethod
    async def deserialize_async(cls, data: bytes):
        return await asyncio.get_running_loop().run_in_executor(None, cls.deserialize, data)


class BaseEnvironmentResolver:
    async def get_environment(self, arguments: Mapping) -> "Environment":
        """
        this is the main reason for environment wrapper's existance.
        give it your specific arguments

        :param arguments:
        :return:
        """
        raise NotImplementedError()

    async def create_container(self,
                               arguments: Mapping,
                               resources_to_use: InvocationResources,
                               ) -> ProcessContainerBase:
        raise NotImplementedError()


class BaseSimpleProcessSpawnEnvironmentResolver(BaseEnvironmentResolver):
    def __init__(self, process_container_factory: ProcessContainerFactoryBase):
        self.__process_container_factory = process_container_factory

    async def create_container(self,
                               arguments: Mapping,
                               resources_to_use: InvocationResources,
                               ) -> ProcessContainerBase:
        return await self.__process_container_factory.create_process_container(
            resources_to_use,
            await self.get_environment(arguments),
        )
