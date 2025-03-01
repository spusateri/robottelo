"""Test class for Remote Execution Management UI

:Requirement: Remoteexecution

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import datetime
import time

import pytest
from broker import VMBroker
from nailgun import entities
from wait_for import wait_for

from robottelo.api.utils import update_vm_host_location
from robottelo.cli.host import Host
from robottelo.config import settings
from robottelo.datafactory import gen_string
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.hosts import ContentHost


def _setup_vm_client_host(vm_client, org_label, subnet_id=None, by_ip=True):
    """Setup a VM host for remote execution.

    :param VMBroker vm_client: where vm_client is VMBroker instance.
    :param str org_label: The organization label.
    :param int subnet: (Optional) Nailgun subnet entity id, to be used by the vm_client host.
    :param bool by_ip: Whether remote execution will use ip or host name to access server.
    """
    vm_client.install_katello_ca()
    vm_client.register_contenthost(org_label, lce='Library')
    assert vm_client.subscribed
    add_remote_execution_ssh_key(vm_client.ip_addr)
    if subnet_id is not None:
        Host.update({'name': vm_client.hostname, 'subnet-id': subnet_id})
    if by_ip:
        # connect to host by ip
        Host.set_parameter(
            {'host': vm_client.hostname, 'name': 'remote_execution_connect_by_ip', 'value': 'True'}
        )


@pytest.fixture(scope='module')
def module_org():
    return entities.Organization().create()


@pytest.fixture(scope='module')
def module_loc(module_org):
    location = entities.Location(organization=[module_org]).create()
    smart_proxy = (
        entities.SmartProxy().search(query={'search': f'name={settings.server.hostname}'})[0].read()
    )
    smart_proxy.location.append(entities.Location(id=location.id))
    smart_proxy.update(['location'])
    return location


@pytest.fixture
def module_vm_client_by_ip(rhel7_host, module_org, module_loc):
    """Setup a VM client to be used in remote execution by ip"""
    _setup_vm_client_host(rhel7_host.host, module_org.label)
    update_vm_host_location(rhel7_host.host, location_id=module_loc.id)
    yield rhel7_host.host


@pytest.mark.libvirt_content_host
@pytest.mark.tier3
def test_positive_run_default_job_template_by_ip(session, module_vm_client_by_ip):
    """Run a job template against a single host by ip

    :id: a21eac46-1a22-472d-b4ce-66097159a868

    :Setup: Use pre-defined job template.

    :Steps:

        1. Navigate to an individual host and click Run Job
        2. Select the job and appropriate template
        3. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :CaseLevel: Integration
    """
    hostname = module_vm_client_by_ip.hostname
    with session:
        assert session.host.search(hostname)[0]['Name'] == hostname
        job_status = session.host.schedule_remote_job(
            [hostname],
            {
                'job_category': 'Commands',
                'job_template': 'Run Command - SSH Default',
                'template_content.command': 'ls',
                'advanced_options.execution_order': 'Randomized',
                'schedule': 'Execute now',
            },
        )
        assert job_status['overview']['job_status'] == 'Success'
        assert job_status['overview']['execution_order'] == 'Execution order: randomized'
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'success'


@pytest.mark.libvirt_content_host
@pytest.mark.tier3
def test_positive_run_custom_job_template_by_ip(session, module_vm_client_by_ip):
    """Run a job template on a host connected by ip

    :id: 3a59eb15-67c4-46e1-ba5f-203496ec0b0c

    :Setup: Create a working job template.

    :Steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Run the job

    :expectedresults: Verify the job was successfully ran against the host

    :CaseLevel: System
    """

    hostname = module_vm_client_by_ip.hostname
    job_template_name = gen_string('alpha')
    with session:
        session.jobtemplate.create(
            {
                'template.name': job_template_name,
                'template.template_editor.rendering_options': 'Editor',
                'template.template_editor.editor': '<%= input("command") %>',
                'job.provider_type': 'SSH',
                'inputs': [{'name': 'command', 'required': True, 'input_type': 'User input'}],
            }
        )
        assert session.jobtemplate.search(job_template_name)[0]['Name'] == job_template_name
        assert session.host.search(hostname)[0]['Name'] == hostname
        job_status = session.host.schedule_remote_job(
            [hostname],
            {
                'job_category': 'Miscellaneous',
                'job_template': job_template_name,
                'template_content.command': 'ls',
                'schedule': 'Execute now',
            },
        )
        assert job_status['overview']['job_status'] == 'Success'
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'success'


@pytest.mark.upgrade
@pytest.mark.libvirt_content_host
@pytest.mark.tier3
def test_positive_run_job_template_multiple_hosts_by_ip(session, module_org, module_loc):
    """Run a job template against multiple hosts by ip

    :id: c4439ec0-bb80-47f6-bc31-fa7193bfbeeb

    :Setup: Create a working job template.

    :Steps:

        1. Set remote_execution_connect_by_ip on hosts to true
        2. Navigate to the hosts page and select at least two hosts
        3. Click the "Select Action"
        4. Select the job and appropriate template
        5. Run the job

    :expectedresults: Verify the job was successfully ran against the hosts

    :CaseLevel: System
    """
    with VMBroker(nick='rhel7', host_classes={'host': ContentHost}, _count=2) as hosts:
        host_names = [client.hostname for client in hosts]
        for client in hosts:
            _setup_vm_client_host(client, module_org.label)
            update_vm_host_location(client, location_id=module_loc.id)
        with session:
            hosts = session.host.search(
                ' or '.join([f'name="{hostname}"' for hostname in host_names])
            )
            assert {host['Name'] for host in hosts} == set(host_names)
            job_status = session.host.schedule_remote_job(
                host_names,
                {
                    'job_category': 'Commands',
                    'job_template': 'Run Command - SSH Default',
                    'template_content.command': 'ls',
                    'schedule': 'Execute now',
                },
            )
            assert job_status['overview']['job_status'] == 'Success'
            assert {host_job['Host'] for host_job in job_status['overview']['hosts_table']} == set(
                host_names
            )
            assert all(
                host_job['Status'] == 'success'
                for host_job in job_status['overview']['hosts_table']
            )


@pytest.mark.libvirt_content_host
@pytest.mark.tier3
def test_positive_run_scheduled_job_template_by_ip(session, module_vm_client_by_ip):
    """Schedule a job to be ran against a host by ip

    :id: 4387bed9-969d-45fb-80c2-b0905bb7f1bd

    :Setup: Use pre-defined job template.

    :Steps:

        1. Set remote_execution_connect_by_ip on host to true
        2. Navigate to an individual host and click Run Job
        3. Select the job and appropriate template
        4. Select "Schedule future execution"
        5. Enter a desired time for the job to run
        6. Click submit

    :expectedresults:

        1. Verify the job was not immediately ran
        2. Verify the job was successfully ran after the designated time

    :CaseLevel: System
    """
    job_time = 5 * 60
    hostname = module_vm_client_by_ip.hostname
    with session:
        assert session.host.search(hostname)[0]['Name'] == hostname
        plan_time = session.browser.get_client_datetime() + datetime.timedelta(seconds=job_time)
        job_status = session.host.schedule_remote_job(
            [hostname],
            {
                'job_category': 'Commands',
                'job_template': 'Run Command - SSH Default',
                'template_content.command': 'ls',
                'schedule': 'Schedule future execution',
                'schedule_content.start_at': plan_time.strftime("%Y-%m-%d %H:%M"),
            },
            wait_for_results=False,
        )
        # Note that to create this host scheduled job we spent some time from that plan_time, as it
        # was calculated before creating the job
        job_left_time = (plan_time - session.browser.get_client_datetime()).total_seconds()
        # assert that we have time left to wait, otherwise we have to use more job time,
        # the job_time must be significantly greater than job creation time.
        assert job_left_time > 0
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'N/A'
        # sleep 3/4 of the left time
        time.sleep(job_left_time * 3 / 4)
        job_status = session.jobinvocation.read('Run ls', hostname, 'overview.hosts_table')
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'N/A'
        # recalculate the job left time to be more accurate
        job_left_time = (plan_time - session.browser.get_client_datetime()).total_seconds()
        # the last read time should not take more than 1/4 of the last left time
        assert job_left_time > 0
        wait_for(
            lambda: session.jobinvocation.read('Run ls', hostname, 'overview.hosts_table')[
                'overview'
            ]['hosts_table'][0]['Status']
            == 'running',
            timeout=(job_left_time + 30),
            delay=1,
        )
        # wait the job to change status to "success"
        wait_for(
            lambda: session.jobinvocation.read('Run ls', hostname, 'overview.hosts_table')[
                'overview'
            ]['hosts_table'][0]['Status']
            == 'success',
            timeout=30,
            delay=1,
        )
        job_status = session.jobinvocation.read('Run ls', hostname, 'overview')
        assert job_status['overview']['job_status'] == 'Success'
        assert job_status['overview']['hosts_table'][0]['Host'] == hostname
        assert job_status['overview']['hosts_table'][0]['Status'] == 'success'
