# -*- encoding: utf-8

import requests
from . import utils
from .users import User
from .works import Work
from .comments import Comments

class AO3(object):
    """A scraper for the Archive of Our Own (AO3)."""

    def __init__(self):
        self.user = None
        self.session = requests.Session()

#bypasses AO3 login to avoid plaintext credential entry
#user can input in their current AO3 session ID

    def login(self, username, cookie):
        """Log in to the archive.
        This allows you to access pages that are only available while
        logged in. Returns True/False to indicate whether the login was successful.
        The cookie should be the value for _otwarchive_session
        """
        self.user = User(username,cookie)
        self.session = self.user.sess
        try:
            rh = self.user.reading_history()
            item = next(rh)
            return True
        except AttributeError:
            return False

    def __repr__(self):
        return '%s()' % (type(self).__name__)


    def work(self, id):
        """Look up a work that's been posted to AO3.
        :param id: the work ID.  In the URL to a work, this is the number.
            e.g. the work ID of http://archiveofourown.org/works/1234 is 1234.
        """
        return Work(id=id, sess=self.session)


    def comments(self, id):
        return Comments(id=id,sess=self.session)

