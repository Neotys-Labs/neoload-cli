import pytest
from click.testing import CliRunner
from docker_test_utils import *

from commands.docker import cli as docker
from commands.docker import key_meta_prior_docker
from commands.docker import resume_prior_attach, is_prior_attach_running, cleanup_after_test, detach_infra
from commands.status import cli as status
from test_prepare import run_prepare_command
from test_forget import run_forget_command

import logging

import json

@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.usefixtures("neoload_login")  # it's like @Before on the neoload_login function
class TestMisc:

    def test_minimal(self, monkeypatch):
        runner = CliRunner()

        def run_prepare_resume_forget(runner, context):
            run_prepare_command(runner, context)
            resume_prior_attach()
            is_prior_attach_running(12345)
            cleanup_after_test()
            run_forget_command(runner, context)

        setup_lifecycle(runner,
            between_create_delete=lambda context: run_prepare_resume_forget(runner, context)
        )


    # keep in mind, this is a negative test, we are purposely causing and looking for an end-to-end failure
    def test_when_invalid_zone(self, monkeypatch):
        runner = CliRunner()

        def mock_test_settings_bork_zone(context, result):

            mock = json.loads(result.output)
            purposeful_error = "BORK"

            # append purposeful_error to the end of the zone codes, to cause containers to error on attach
            lgs = mock['lgZoneIds']
            first_key = list(lgs.keys())[0]
            first_value = lgs[first_key]
            lg = lgs.pop(first_key)
            lgs[first_key+purposeful_error] = first_value
            mock['lgZoneIds'] = lgs
            mock['controllerZoneId'] = mock['controllerZoneId'] + purposeful_error
            context['mock_test_setting'] = mock

            mock_api_get(monkeypatch, 'v2/tests/%s' % mock['id'], json.dumps(mock))

        def validate_borked_attach(context, result):

            assert 'The provided zone identifier is not valid' in result.output
            assert_failure(result)

            # set up the list of tests to include the same fake test-setting for the next step
            mock_api_get(monkeypatch, 'v2/tests', json.dumps([context['mock_test_setting']]))

        setup_lifecycle(runner,
            after_create=mock_test_settings_bork_zone,
            between_create_delete=lambda context: attach_detach_lifecycle(context,
                after_attach=validate_borked_attach,
                between_attach_detach=lambda context: True # cause waiting
            )
        )
