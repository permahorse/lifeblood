import json

import shutil
from pathlib import Path

from lifeblood.enums import SpawnStatus
from lifeblood_testing_common.nodes_common import TestCaseBase, PseudoContext
import tempfile
from unittest import mock


class TestHouRop(TestCaseBase):
    def setUp(self):
        self._tmp_path = Path(tempfile.mkdtemp('unittest'))

    def tearDown(self):
        shutil.rmtree(self._tmp_path)

    async def test_hip_usd_generator_simple_no_checkpoint(self):
        await self._helper_test_hip_usd_generator_simple(False)

    async def test_hip_usd_generator_simple_checkpoint(self):
        await self._helper_test_hip_usd_generator_simple(True)

    async def _helper_test_hip_usd_generator_simple(self, do_checkpoint: bool = False):
        await self._helper_test_simple(
            node_type='hip_usd_generator',
            hip_json={
                'bad_frames': [],
                'default_output': str(self._tmp_path / 'out'),
            },
            node_parms={
                'hip path': (self._tmp_path / 'test.hip'),
                'scene file output': (self._tmp_path / 'delme.$F4.usd'),
                'do checkpoint': do_checkpoint,
                'driver path': '/rop/driver',
            },
        )

    async def test_hip_usd_generator_checkpoint_crash_continue(self):
        await self._helper_test_hip_usd_generator_checkpoint_continue_discard(
            first_do_checkpoint=True,
            second_do_checkpoint=True,
            expect_checkpoint_continue=True,
        )

    async def test_hip_usd_generator_no_checkpoint_crash_continue(self):
        await self._helper_test_hip_usd_generator_checkpoint_continue_discard(
            first_do_checkpoint=False,
            second_do_checkpoint=False,
            expect_checkpoint_continue=False,
        )
    
    async def test_hip_usd_generator_discard_checkpoint_different_hip_name(self):
        await self._helper_test_hip_usd_generator_checkpoint_continue_discard(
            second_file_name='test1.hip',
            expect_checkpoint_continue=False,
        )

    async def test_hip_usd_generator_discard_checkpoint_different_params(self):
        await self._helper_test_hip_usd_generator_checkpoint_continue_discard(
            second_driver_path='/rop/anotherdriver',
            expect_checkpoint_continue=False,
        )

    async def test_hip_usd_generator_checkpoint_crash_continue_with_spawned(self):
        await self._helper_test_hip_usd_generator_checkpoint_continue_discard(
            first_do_checkpoint=True,
            second_do_checkpoint=True,
            expect_checkpoint_continue=True,
            connect_spawned=True,
        )

    async def test_hip_usd_generator_no_checkpoint_crash_continue_with_spawned(self):
        await self._helper_test_hip_usd_generator_checkpoint_continue_discard(
            first_do_checkpoint=False,
            second_do_checkpoint=False,
            expect_checkpoint_continue=False,
            connect_spawned=True,
        )

    async def test_hip_usd_generator_discard_checkpoint_different_hip_name_with_spawned(self):
        await self._helper_test_hip_usd_generator_checkpoint_continue_discard(
            second_file_name='test1.hip',
            expect_checkpoint_continue=False,
            connect_spawned=True,
        )

    async def test_hip_usd_generator_discard_checkpoint_different_params_with_spawned(self):
        await self._helper_test_hip_usd_generator_checkpoint_continue_discard(
            second_driver_path='/rop/anotherdriver',
            expect_checkpoint_continue=False,
            connect_spawned=True,
        )

    #
    # hip_driver_renderer
    #

    async def test_hip_driver_renderer_simple_no_checkpoint(self):
        await self._helper_test_hip_driver_renderer_simple(False)

    async def test_hip_driver_renderer_simple_checkpoint(self):
        await self._helper_test_hip_driver_renderer_simple(True)

    async def test_hip_driver_renderer_checkpoint_crash_continue(self):
        await self._helper_test_hip_driver_renderer_checkpoint_continue_discard(
            first_do_checkpoint=True,
            second_do_checkpoint=True,
            expect_checkpoint_continue=True,
        )

    async def test_hip_driver_renderer_no_checkpoint_crash_continue(self):
        await self._helper_test_hip_driver_renderer_checkpoint_continue_discard(
            first_do_checkpoint=False,
            second_do_checkpoint=False,
            expect_checkpoint_continue=False,
        )

    async def test_hip_driver_renderer_discard_checkpoint_different_hip_name(self):
        await self._helper_test_hip_driver_renderer_checkpoint_continue_discard(
            second_file_name='test1.hip',
            expect_checkpoint_continue=False,
        )

    async def test_hip_driver_renderer_discard_checkpoint_different_params(self):
        await self._helper_test_hip_driver_renderer_checkpoint_continue_discard(
            second_driver_path='/rop/anotherdriver',
            expect_checkpoint_continue=False,
        )

    async def test_hip_driver_renderer_checkpoint_crash_continue_with_spawned(self):
        await self._helper_test_hip_driver_renderer_checkpoint_continue_discard(
            first_do_checkpoint=True,
            second_do_checkpoint=True,
            expect_checkpoint_continue=True,
            connect_spawned=True,
        )

    async def test_hip_driver_renderer_no_checkpoint_crash_continue_with_spawned(self):
        await self._helper_test_hip_driver_renderer_checkpoint_continue_discard(
            first_do_checkpoint=False,
            second_do_checkpoint=False,
            expect_checkpoint_continue=False,
            connect_spawned=True,
        )

    async def test_hip_driver_renderer_discard_checkpoint_different_hip_name_with_spawned(self):
        await self._helper_test_hip_driver_renderer_checkpoint_continue_discard(
            second_file_name='test1.hip',
            expect_checkpoint_continue=False,
            connect_spawned=True,
        )

    async def test_hip_driver_renderer_discard_checkpoint_different_params_with_spawned(self):
        await self._helper_test_hip_driver_renderer_checkpoint_continue_discard(
            second_driver_path='/rop/anotherdriver',
            expect_checkpoint_continue=False,
            connect_spawned=True,
        )

    #
    #
    #

    # hip_usd_generator helpers

    async def _helper_test_hip_usd_generator_checkpoint_continue_discard(
            self,
            *,
            first_file_name: str = 'test.hip',
            second_file_name: str = 'test.hip',
            first_driver_path: str = '/rop/driver',
            second_driver_path: str = '/rop/driver',
            second_extra_node_parms: dict | None = None,
            first_do_checkpoint=True,
            second_do_checkpoint=True,
            expect_checkpoint_continue: bool = True,
            connect_spawned: bool = False,
    ):
        if second_extra_node_parms is None:
            second_extra_node_parms = {}
        if expect_checkpoint_continue:
            expected_lines = [
                    f'{first_driver_path} ::: 1234',
                    f'{second_driver_path} ::: 12',
                    f'{second_driver_path} ::: 333',
                ]
        else:
            expected_lines = [
                    f'{first_driver_path} ::: 1234',
                    f'{second_driver_path} ::: 1234',
                    f'{second_driver_path} ::: 12',
                    f'{second_driver_path} ::: 333',
                ]
        common_driver_data = {
            'parms': {
                'mkpath': False,
                'runcommand': False,
                'husk_mplay': False,
                'savetodirectory_directory': '',
                'lopoutput': 'loplop',
                'take': '<main>',
                'outputimage': '/foo/bar',
            },
        }
        await self._helper_test_checkpoint_continue_discard(
            node_type='hip_usd_generator',
            first_file_name=first_file_name,
            second_file_name=second_file_name,
            first_hip_json={
                'bad_frames': [12],
                'default_output': str(self._tmp_path / 'out'),
                'nodes': {
                    first_driver_path: common_driver_data,
                },
            },
            second_hip_json={
                'bad_frames': [],
                'default_output': str(self._tmp_path / 'out'),
                'nodes': {
                    second_driver_path: common_driver_data,
                },
            },
            first_node_parms={
                'hip path': (self._tmp_path / first_file_name),
                'scene file output': (self._tmp_path / 'delme.$F4.usd'),
                'do checkpoint': first_do_checkpoint,
                'driver path': first_driver_path,
            },
            second_node_parms={
                'hip path': (self._tmp_path / second_file_name),
                'scene file output': (self._tmp_path / 'delme.$F4.usd'),
                'do checkpoint': second_do_checkpoint,
                'driver path': second_driver_path,
                **second_extra_node_parms,
            },
            expect_checkpoint_to_exist_after_first=first_do_checkpoint,
            expected_driver_lines=expected_lines,
            connect_spawned=connect_spawned,
            expected_spawn_count=len(expected_lines) if connect_spawned else 0,
        )

    # hip_driver_renderer helpers

    async def _helper_test_hip_driver_renderer_simple(self, do_checkpoint: bool = False):
        await self._helper_test_simple(
            node_type='hip_driver_renderer',
            hip_json={
                'bad_frames': [],
                'default_output': str(self._tmp_path / 'out'),
                'nodes': {
                    '/rop/driver': {
                        'parms': {
                            'fakeoutparm': str(self._tmp_path / 'delme.$F4.usd'),
                        }
                    }
                }
            },
            node_parms={
                'hip path': (self._tmp_path / 'test.hip'),
                'do override parmname': True,
                'override parmname': 'fakeoutparm',
                'do checkpoint': do_checkpoint,
                'driver path': '/rop/driver',
            },
        )

    async def _helper_test_hip_driver_renderer_checkpoint_continue_discard(
            self,
            *,
            first_file_name: str = 'test.hip',
            second_file_name: str = 'test.hip',
            first_driver_path: str = '/rop/driver',
            second_driver_path: str = '/rop/driver',
            second_extra_node_parms: dict | None = None,
            first_do_checkpoint=True,
            second_do_checkpoint=True,
            expect_checkpoint_continue: bool = True,
            connect_spawned: bool = False,
    ):
        if second_extra_node_parms is None:
            second_extra_node_parms = {}
        if expect_checkpoint_continue:
            expected_lines = [
                    f'{first_driver_path} ::: 1234',
                    f'{second_driver_path} ::: 12',
                    f'{second_driver_path} ::: 333',
                ]
        else:
            expected_lines = [
                    f'{first_driver_path} ::: 1234',
                    f'{second_driver_path} ::: 1234',
                    f'{second_driver_path} ::: 12',
                    f'{second_driver_path} ::: 333',
                ]
        await self._helper_test_checkpoint_continue_discard(
            node_type='hip_driver_renderer',
            first_file_name=first_file_name,
            second_file_name=second_file_name,
            first_hip_json={
                'bad_frames': [12],
                'default_output': str(self._tmp_path / 'out'),
                'nodes': {
                    first_driver_path: {
                        'parms': {
                            'fakeoutparm': str(self._tmp_path / 'delme.$F4.usd'),
                        }
                    }
                }
            },
            second_hip_json={
                'bad_frames': [],
                'default_output': str(self._tmp_path / 'out'),
                'nodes': {
                    second_driver_path: {
                        'parms': {
                            'fakeoutparm': str(self._tmp_path / 'delme.$F4.usd'),
                        }
                    }
                }
            },
            first_node_parms={
                'hip path': (self._tmp_path / first_file_name),
                'do override parmname': True,
                'override parmname': 'fakeoutparm',
                'do checkpoint': first_do_checkpoint,
                'driver path': first_driver_path,
            },
            second_node_parms={
                'hip path': (self._tmp_path / second_file_name),
                'do override parmname': True,
                'override parmname': 'fakeoutparm',
                'do checkpoint': second_do_checkpoint,
                'driver path': second_driver_path,
                **second_extra_node_parms,
            },
            expect_checkpoint_to_exist_after_first=first_do_checkpoint,
            expected_driver_lines=expected_lines,
            connect_spawned=connect_spawned,
            expected_spawn_count=len(expected_lines) if connect_spawned else 0,
        )

    #
    # Generic Helpers
    #

    async def _helper_test_simple(
            self,
            node_type: str,
            hip_json: dict,
            node_parms: dict,
    ):
        (self._tmp_path / 'out').mkdir()
        with open(self._tmp_path / 'test.hip', 'w') as f:
            json.dump(hip_json, f)

        await self._helper_test_simple_invocation(
            node_type,
            [node_parms],
            {
                'frames': [1234, 12, 333],
            },
            add_relative_to_PATH=Path(__file__).parent / 'data' / 'mock_houdini',
            commands_to_replace_with_py_mock=['hython'],
        )

        render_log_path = self._tmp_path / 'out' / 'render_log'
        self.assertTrue(render_log_path.exists())
        lines = render_log_path.read_text().splitlines(keepends=False)
        self.assertEqual(
            [
                '/rop/driver ::: 1234',
                '/rop/driver ::: 12',
                '/rop/driver ::: 333',
            ],
            lines,
        )

    async def _helper_test_checkpoint_continue_discard(
            self,
            *,
            node_type: str,
            first_file_name: str = 'test.hip',
            second_file_name: str = 'test.hip',
            first_hip_json: dict,
            second_hip_json: dict,
            first_node_parms: dict,
            second_node_parms: dict,
            expect_checkpoint_to_exist_after_first: bool,
            expected_driver_lines: list[str],
            connect_spawned: bool,
            expected_spawn_count: int = 0,
    ):
        (self._tmp_path / 'out').mkdir()
        with open(self._tmp_path / first_file_name, 'w') as f:
            json.dump(first_hip_json, f)

        checkpoint_path = self._tmp_path / f'task-{1}-{1}.chkpt'
        extra_nodes_to_create = []
        if connect_spawned:
            extra_nodes_to_create = [('null', [(1, 'spawned', 2, 'main')])]
        spawn_call_count = 0
        with mock.patch('lifeblood.scheduler.scheduler.Scheduler.spawn_tasks') as spawn_patch:
            spawn_patch.return_value = (SpawnStatus.SUCCEEDED, 999)
            await self._helper_test_simple_invocation(
                node_type,
                [first_node_parms],
                {
                    'frames': [1234, 12, 333],
                },
                add_relative_to_PATH=Path(__file__).parent / 'data' / 'mock_houdini',
                commands_to_replace_with_py_mock=['hython'],
                expected_task_exit_code=1,
                extra_nodes_to_create=extra_nodes_to_create,
            )
            spawn_call_count += spawn_patch.call_count
        self.assertEqual(expect_checkpoint_to_exist_after_first, checkpoint_path.exists())

        with open(self._tmp_path / second_file_name, 'w') as f:
            json.dump(second_hip_json, f)

        # now run again, expect to continue from checkpoint
        with mock.patch('lifeblood.scheduler.scheduler.Scheduler.spawn_tasks') as spawn_patch:
            spawn_patch.return_value = (SpawnStatus.SUCCEEDED, 999)
            await self._helper_test_simple_invocation(
                node_type,
                [second_node_parms],
                {
                    'frames': [1234, 12, 333],
                },
                add_relative_to_PATH=Path(__file__).parent / 'data' / 'mock_houdini',
                commands_to_replace_with_py_mock=['hython'],
                extra_nodes_to_create=extra_nodes_to_create,
            )
            spawn_call_count += spawn_patch.call_count
        self.assertFalse(checkpoint_path.exists())

        # now we expect no duplicated lines in log
        render_log_path = self._tmp_path / 'out' / 'render_log'
        self.assertTrue(render_log_path.exists())
        lines = render_log_path.read_text().splitlines(keepends=False)

        self.assertEqual(
            expected_driver_lines,
            lines
        )

        self.assertEqual(expected_spawn_count, spawn_call_count)
