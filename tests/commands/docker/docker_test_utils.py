
from commands.docker import cli as docker

from commands.test_settings import cli as settings
from commands.status import cli as status
from commands.login import cli as login
from commands.zones import cli as zones

from helpers.test_utils import *
import logging
import traceback
import sys

import json

# note: there's really no good/fast way to mock responses related to infra attach/detach
# from the NLW server, at least in this context. the mock_api_post is scoped to requests
# from python, not system-wide, so the docker containers would need to be proxied to loopback :O=


# the reason this is it's own function is that login + test-settings + zone semantics apply to multiple tests
def setup_lifecycle(runner, before_create=None, after_create=None, between_create_delete=None, before_delete=None, after_delete=None):

    catches = []

    #  list zones, pick first static one, prefer a zone with no existing resources
    result_zone_ls = runner.invoke(zones,['--static'])
    listing = json.loads(result_zone_ls.output)
    fn_prefer = lambda x: (len(x['controllers'])+len(x['loadgenerators']))
    listing = sorted(listing, key=fn_prefer)
    found = next(iter(listing), None)

    assert found is not None

    print("Found zone: " + found['name'] + " [" + found['id'] + "]")

    num_of_lgs = 1
    test_name = generate_test_settings_name()
    #! create a temp test with unique name

    context = {
        'runner': runner,
        'zone': found,
        'test_name': test_name,
        'num_of_lgs': num_of_lgs
    }

    if before_create is not None: before_create(context)

    create_success = False

    try:
        if before_create is not None: before_create(context)


        create_result = runner.invoke(settings, [
            'create', test_name,
            '--zone', found['id'],
            '--lgs', found['id']+':'+str(num_of_lgs),
            '--scenario', 'sanityScenario'
        ])
        assert_success(create_result)
        create_success = True

        if after_create is not None: after_create(context, create_result)

    except Exception as err:
        catches.append(err)

    if between_create_delete is not None:
        try:
            between_create_delete(context)
        except Exception as err:
            catches.append(err)

    if create_success:
        try: # ensure that errors from top-level code don't impact the imperative to delete temp settings
            if before_delete is not None: before_delete(context)
        except Exception as err:
            catches.append(err)

        try:
            delete_result = runner.invoke(settings, [
                'delete', test_name
            ])
            assert_success(delete_result)

            if after_delete is not None: after_delete(context, delete_result)

        except Exception as err:
            catches.append(err)

    if len(catches) > 0:
        raise catches[0] #Exception("\n".join(map(lambda err: repr(err),catches)))


# the reason this is it's own function is because for any attach, there should be a detach; hermetic setup/teardown
def attach_detach_lifecycle(context, before_attach=None, after_attach=None, between_attach_detach=None, before_detach=None, after_detach=None):

    catches = []
    runner = context['runner']

    attach_success = False
    attach_result = None
    try:
        if before_attach is not None: before_attach(context)

        args = ['attach']

        if between_attach_detach is None: args.insert(0, "--nowait")

        attach_result = runner.invoke(docker, args)
        attach_success = True

    except Exception as err:
        logging.error("Failed in attach_detach_lifecycle::attach[0]" + str(err))
        catches.append(err)

    try:
        if after_attach is not None: after_attach(context, attach_result)
    except Exception as err:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        ex_str = repr(traceback.format_exception(exc_type, exc_value,exc_traceback))
        logging.error("Failed in attach_detach_lifecycle::attach[1]" + ex_str)
        catches.append(err)

    if between_attach_detach is not None:
        try:
            between_attach_detach(context)
        except Exception as err:
            catches.append(err)

    if attach_success:
        try: # ensure that errors from top-level code don't impact the imperative to detach testing infra
            if before_detach is not None: before_detach(context)
        except Exception as err:
            catches.append(err)

        try:
            detach_result = runner.invoke(docker, ['--all','detach'])
            print(detach_result.output)
            assert_success(detach_result)

            if after_detach is not None: after_detach(context, detach_result)

        except Exception as err:
            logging.error("Failed in attach_detach_lifecycle::detach")
            catches.append(err)

    if len(catches) > 0:
        raise catches[0] #Exception("\n".join(map(lambda err: repr(err),catches)))
