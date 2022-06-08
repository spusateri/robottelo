"""Test Hosts Content related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Host-Content

:Assignee: spusater

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker.broker import VMBroker
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import get_entity_data

from robottelo.hosts import ContentHost


class TestScenarioDBseedHostMismatch:
    """This test scenenario veryfies that the upgrade succeeds even when inconsistencies exist
    in the database between Organization, Location and Content Host.

    Test Steps:

        1. Before Satellite upgrade
        2. Create a New Organization and Location
        3. Create a Content Host in the Organization
        4. Ensure the Org is not in the Location
        4. Assign the Content Host to the Location using the rake console
        7. Ensure the Host is in both but the Org is not in Location, creating a mismatch
        8. Upgrade Satellite
        9. Ensure upgrade succeeds

    BZ: 2043705, 2028786, 2019467
    """

    @pytest.mark.pre_upgrade
    def test_pre_db_seed_host_mismatch(self, target_sat):
        """
        :id: 28861b9f-8abd-4efc-bfd5-40b7e825a941

        :steps:
            1. Create a Location
            2. Create an Org and ensure the Org is not in the Location
            3. Create a Content Host on Org
            4. Use rake console to assign the Content Host to the Location
            5. Ensure the mismatch is created for Content Host when Org is not in the Location
            6. Do the upgrade

        :expectedresults:
            1. The Content Host is assigned to both Location and Org, but Org is not in Location

        :BZ: 2043705, 2028786, 2019467

        :customerscenario: true
        """
        org = target_sat.api.Organization().create()
        loc = target_sat.api.Location().create()

        chost_vm = VMBroker(nick='rhel7', host_classes={'host': ContentHost}).checkout()

        chost_vm.install_katello_ca(target_sat)
        chost_vm.register_contenthost(org=org.label, lce='Library')

        chost = target_sat.api.Host().search(query={'search': chost_vm.hostname})

        assert chost[0].organization.id == org.id

        # Now we need to break the taxonomy between chost, org and location
        rake_host = f"host = ::Host.find({chost[0].id})"
        rake_organization = f"; host.location_id={loc.id}"
        rake_host_save = "; host.save!"
        result = target_sat.run(
            f"echo '{rake_host}{rake_organization}{rake_host_save}' | foreman-rake console"
        )

        assert 'true' in result.stdout
        chost = target_sat.api.Host().search(query={'search': chost_vm.hostname})
        assert chost[0].location.id == loc.id

        global_dict = {
            self.__class__.__name__: {
                'client_name': chost_vm.hostname,
                'organization_id': org.id,
                'location_id': loc.id,
            }
        }

        create_dict(global_dict)

    @pytest.mark.post_upgrade(depend_on=test_pre_db_seed_host_mismatch)
    def test_post_db_seed_host_mismatch(self, target_sat):
        """Check whether the upgrade succeeds, and ensure Content Host
        exists on the Satellite and has not had any attributes changed
        """
        chostname = get_entity_data(self.__class__.__name__)['client_name']
        org_id = get_entity_data(self.__class__.__name__)['organization_id']
        loc_id = get_entity_data(self.__class__.__name__)['location_id']
        chost = target_sat.api.Host().search(query={'search': chostname})

        assert org_id == chost[0].organization.id
        assert loc_id == chost[0].location.id

        VMBroker(host=chost).checkin()
