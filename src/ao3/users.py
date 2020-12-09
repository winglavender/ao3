from datetime import datetime
import collections
import itertools
import re

from bs4 import BeautifulSoup, Tag
import requests


class User(object):

    def __init__(self, username, cookie):
        self.username = username
        sess = requests.Session()
#        req = sess.post('https://archiveofourown.org/user_sessions', params={
#            'user_session[login]': username,
#            'user_session[password]': password,
#        })

        # Unfortunately AO3 doesn't use HTTP status codes to communicate
        # results -- it's a 200 even if the login fails.
#        if 'Please try again' in req.text:
#            raise RuntimeError(
#                'Error logging in to AO3; is your password correct?')
        jar=requests.cookies.RequestsCookieJar()
        jar.set('_otwarchive_session',cookie,domain='archiveofourown.org')  #must be done separately bc the set func returns a cookie, not a jar
        jar.set('user_credentials','1',domain='archiveofourown.org')
        sess.cookies=jar

        self.sess = sess

    def __repr__(self):
        return '%s(username=%r)' % (type(self).__name__, self.username)

    def reading_history(self):
        """Returns a list of articles in the user's reading history.

        This requires the user to turn on the Viewing History feature.

        Generates a tuple of  work_id, date, numvisits,title,author,fandom,warnings,relationships,characters,freeforms,words,chapters,comments,kudos,bookmarks,hits

        """
        # TODO: What happens if you don't have this feature enabled?

        # URL for the user's reading history page
        api_url = (
            'https://archiveofourown.org/users/%s/readings?page=%%d' %
            self.username)

        for page_no in itertools.count(start=1):
            req = self.sess.get(api_url % page_no)
            #if timeout, wait and try again



            soup = BeautifulSoup(req.text, features='html.parser')

            # The entries are stored in a list of the form:
            #
            #     <ol class="reading work index group">
            #       <li id="work_12345" class="reading work blurb group">
            #         ...
            #       </li>
            #       <li id="work_67890" class="reading work blurb group">
            #         ...
            #       </li>
            #       ...
            #     </ol>
            #
            ol_tag = soup.find('ol', attrs={'class': 'reading'})
            for li_tag in ol_tag.findAll('li', attrs={'class': 'blurb'}):
                try:
                    work_id = li_tag.attrs['id'].replace('work_', '')

                    # Within the <li>, the last viewed date is stored as
                    #
                    #     <h4 class="viewed heading">
                    #         <span>Last viewed:</span> 24 Dec 2012
                    #
                    #         (Latest version.)
                    #
                    #         Viewed once
                    #     </h4>
                    #
                    h4_tag = li_tag.find('h4', attrs={'class': 'viewed'})
                    date_str = re.search(
                        r'[0-9]{1,2} [A-Z][a-z]+ [0-9]{4}',
                        h4_tag.contents[2]).group(0)
                    date = datetime.strptime(date_str, '%d %b %Y').date()
                    
                    if "Visited once" in h4_tag.contents[2]:
                        numvisits='1' #keeping as strings bc intend to print this to a file
                    else:
                        numvisits=re.search(r'Visited (\d*) times',h4_tag.contents[2]).group(1)

                    title=li_tag.find('h4', attrs={'class':'heading'}).find('a').contents[0]

                    author=[] #this is if there's multiple authors
                    author_tag=li_tag.find('h4', attrs={'class':'heading'})
                    for x in author_tag.find_all('a',attrs={'rel':'author'}):
                        author.append(x.contents[0])

                    fandom=[]
                    fandom_tag=li_tag.find('h5',attrs={'class':'fandoms'})
                    for x in fandom_tag.find_all('a',attrs={'class':'tag'}):
                        fandom.append(x.contents[0])

                    warnings=[]
                    for x in li_tag.find_all('li',attrs={'class':'warnings'}):
                        warnings.append(x.find('a').contents[0])
                    relationships=[]
                    for x in li_tag.find_all('li',attrs={'class':'relationships'}):
                        relationships.append(x.find('a').contents[0])
                    characters=[]
                    for x in li_tag.find_all('li',attrs={'class':'characters'}):
                        characters.append(x.find('a').contents[0])
                    freeforms=[]
                    for x in li_tag.find_all('li',attrs={'class':'freeforms'}):
                        freeforms.append(x.find('a').contents[0])

                    words=li_tag.find('dd',attrs={'class','words'}).contents[0]
                    chapters=li_tag.find('dd',attrs={'class','chapters'})
                    if chapters.find('a') is not None:
                        chapters.find('a').replaceWithChildren()
                    chapters=''.join(chapters.contents)
                    comments=li_tag.find('dd',attrs={'class','comments'}).contents[0].contents[0]
                    kudos=li_tag.find('dd',attrs={'class','kudos'}).contents[0].contents[0]
                    bookmarks=li_tag.find('dd',attrs={'class','bookmarks'}).contents[0].contents[0]
                    hits=li_tag.find('dd',attrs={'class','hits'}).contents[0]

                    yield work_id, date, numvisits,title,author,fandom,warnings,relationships,characters,freeforms,words,chapters,comments,kudos,bookmarks,hits

                except KeyError:
                    # A deleted work shows up as
                    #
                    #      <li class="deleted reading work blurb group">
                    #
                    # There's nothing that we can do about that, so just skip
                    # over it.
                    if 'deleted' in li_tag.attrs['class']:
                        pass
                    else:
                        raise

            # The pagination button at the end of the page is of the form
            #
            #     <li class="next" title="next"> ... </li>
            #
            # If there's another page of results, this contains an <a> tag
            # pointing to the next page.  Otherwise, it contains a <span>
            # tag with the 'disabled' class.
            next_button = soup.find('li', attrs={'class': 'next'})
            if next_button.find('span', attrs={'class': 'disabled'}):
                break
