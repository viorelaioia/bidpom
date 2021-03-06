#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from browserid import BrowserID
from mocks.user import MockUser
import restmail


class BaseTest(object):

    _persona_login_button_locator = (By.CSS_SELECTOR, 'button.btn-persona')
    _persona_logged_in_indicator_locator = (By.ID, 'loggedin')
    _persona_log_out_link_locator = (By.CSS_SELECTOR, '#loggedin a')

    def browserid_url(self, base_url):
        response = requests.get('%s/' % base_url, verify=False)
        match = re.search(BrowserID.INCLUDE_URL_REGEX, response.content)
        if match:
            return match.group(1)
        else:
            raise Exception('Unable to determine BrowserID URL from %s.' % base_url)

    def log_out(self, selenium, timeout):
        WebDriverWait(selenium, timeout).until(
            lambda s: s.find_element(*self._persona_logged_in_indicator_locator).is_displayed())
        selenium.find_element(*self._persona_log_out_link_locator).click()
        WebDriverWait(selenium, timeout).until(
            lambda s: s.find_element(*self._persona_login_button_locator).is_displayed())

    def create_verified_user(self, selenium, timeout):
        user = MockUser()
        from browserid.pages.sign_in import SignIn
        signin = SignIn(selenium, timeout)
        signin.sign_in_new_user(user.primary_email, user.password)
        mail = restmail.get_mail(user.primary_email, timeout=timeout)
        verify_url = re.search(BrowserID.VERIFY_URL_REGEX,
                               mail[0]['text']).group(0)

        selenium.get(verify_url)
        from browserid.pages.complete_registration import CompleteRegistration
        complete_registration = CompleteRegistration(selenium,
                                                     timeout,
                                                     expect='success')
        assert user['primary_email'] in complete_registration.user_loggedin
        return user

    def email_appears_valid(self, email_text):
        assert 'Click' in email_text and 'link' in email_text, \
            'The strings "Click" and "link" were not found in %s' % email_text
