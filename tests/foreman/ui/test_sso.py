# -*- encoding: utf-8 -*-
"""Test class for installer (UI)"""

from robottelo.decorators import stubbed
from robottelo.test import UITestCase


class TestSSOUI(UITestCase):
    # Notes for SSO testing:
    # Of interest... In some test cases I've placed a few comments prefaced
    # with "devnote:" These are -- obviously -- notes from developers that
    # might help reiterate something important or a reminder of way(s) to test
    # something.

    # There may well be more cases that I have missed for this feature, and
    # possibly other LDAP types. These (in particular, the LDAP variations)
    # can be easily added later.

    # What is SSO?
    # Once (IPA or AD) user logs in to linux or windows client which is
    # IPA/AD enrolled, there should be no need for the user to again
    # authenticate at the Sat61 WebUI Login form with (IPA or AD user) login
    # details. Instead the IPA or AD user should be able to simply log-in to
    # the Sat61 WebUI automatically upon accessing the sat61 URL.

    # More detailed information at:
    # External authentication:
    # http://theforeman.org/manuals/1.8/index.html#5.7ExternalAuthentication
    # LDAP authentication:
    # http://theforeman.org/manuals/1.8/index.html#4.1.1LDAPAuthentication

    @stubbed()
    def test_sso_kerberos_basic_no_roles(self):
        """@test: SSO - kerberos (IdM or AD) login (basic) that has no roles

        @feature: SSO or External Authentication

        @setup: Assure SSO with kerberos (IdM or AD) is set up.

        @steps:
        1. Login using a kerberos (IdM or AD) ID to the client
        2. Login to the Web-UI should be automatic without the need to fill in
        the form.

        @assert: Log in to sat6 UI successfully but cannot access anything
        useful in UI

        @status: Manual

        """

    @stubbed()
    def test_sso_kerberos_basic_roles(self):
        """@test: SSO - kerberos (IdM or AD) login (basic) that has roles
        assigned.

        @feature: SSO or External Authentication

        @setup: Assure SSO with kerberos (IdM or AD) is set up.

        @steps:
        1. Login using a kerberos (IdM or AD) ID to the client
        2. Login to the Web-UI should be automatic without the need to fill in
        the form.

        @assert: Log in to sat6 UI successfully and can access functional
        areas in UI

        @status: Manual

        """

    @stubbed()
    def test_sso_kerberos_user_disabled(self):
        """@test: Kerberos (IdM or AD) user activity when kerb (IdM or AD)
        account has been deleted or deactivated.

        @feature: SSO or External Authentication

        @steps:
        1. Login to the foreman UI
        2. Delete or disable userid on IdM server or AD side.

        @assert: This is handled gracefully (user is logged out perhaps?)
        and no data corruption

        @status: Manual

        """
