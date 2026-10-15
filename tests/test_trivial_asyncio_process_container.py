import sys
import os
import shutil
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, mock
from lifeblood.impl.trivial_asyncio_process_container import TrivialAsyncioProcessContainerFactory
from lifeblood.invocationjob import Environment
from lifeblood.process_utils import oh_no_its_windows


class TestTrivialAsyncioProcessContainer(IsolatedAsyncioTestCase):
    if oh_no_its_windows:
        @staticmethod
        def normalize_path(x: str):
            """
            stoopid windows...
            """
            x = x.lower()
            if os.path.splitext(x)[1] != '.exe':
                x += '.exe'
            return x
    else:
        @staticmethod
        def normalize_path(x: str):
            return x

    async def test_create_process_no_python(self):
        container = await TrivialAsyncioProcessContainerFactory().create_process_container(None, Environment())

        with mock.patch('lifeblood.impl.trivial_asyncio_process_container.create_process') as m:
            await container.create_process(['python', '/foo/bar'], env=None, cwd=None)

        self.assertTrue(m.called)

        self.assertEqual(
            self.normalize_path(sys.executable),
            self.normalize_path(shutil.which(m.call_args[0][0][0], path=m.call_args[0][1].get('PATH', None)))
        )

    async def test_create_process_yes_python_env_in_base_env(self):
        expected_python = Path(__file__).parent / 'data' / 'fake_bin' / 'python'
        container = await TrivialAsyncioProcessContainerFactory().create_process_container(None, Environment({'PATH': str(expected_python.parent)}))

        with mock.patch('lifeblood.impl.trivial_asyncio_process_container.create_process') as m:
            await container.create_process(['python', '/foo/bar'], env=None, cwd=None)

        self.assertTrue(m.called)
        self.assertEqual(
            self.normalize_path(str(expected_python)),
            self.normalize_path(shutil.which(m.call_args[0][0][0], path=m.call_args[0][1].get('PATH', None)))
        )

    async def test_create_process_yes_python_env_in_create_process(self):
        expected_python = Path(__file__).parent / 'data' / 'fake_bin' / 'python'
        container = await TrivialAsyncioProcessContainerFactory().create_process_container(None, Environment())

        with mock.patch('lifeblood.impl.trivial_asyncio_process_container.create_process') as m:
            await container.create_process(['python', '/foo/bar'], env=Environment({'PATH': str(expected_python.parent)}), cwd=None)

        self.assertTrue(m.called)
        self.assertEqual(
            self.normalize_path(str(expected_python)),
            self.normalize_path(shutil.which(m.call_args[0][0][0], path=m.call_args[0][1].get('PATH', None)))
        )