from datetime import datetime
import collections
import itertools
import re
import time

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

        self.deleted = 0 #just for curiosity, count how many times deleted or locked works appear

    def __repr__(self):
        return '%s(username=%r)' % (type(self).__name__, self.username)

    def reading_history(self):
        """Returns a list of articles in the user's reading history.

        This requires the user to turn on the Viewing History feature.

        Generates a tuple of work_id,date,numvisits,title,author,fandom,warnings,relationships,characters,freeforms,words,chapters,comments,kudos,bookmarks,hits,pubdate

        """
        # TODO: What happens if you don't have this feature enabled?

        # URL for the user's reading history page
        api_url = (
            'https://archiveofourown.org/users/%s/readings?page=%%d' %
            self.username)

        for page_no in itertools.count(start=1):
            req = self.sess.get(api_url % page_no)
            print("On page: "+str(page_no))
            print("Cumulative deleted works encountered: "+str(self.deleted))
            #if timeout, wait and try again
            while len(req.text) < 20 and "Retry later" in req.text:
                print("timeout... waiting 3 mins and trying again")
                time.sleep(180) 
                req = self.sess.get(api_url % page_no)

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

                    #cast all the beautifulsoup navigablestrings to strings
                    title=str(li_tag.find('h4', attrs={'class':'heading'}).find('a').contents[0])

                    author=[] #this is if there's multiple authors
                    author_tag=li_tag.find('h4', attrs={'class':'heading'})
                    for x in author_tag.find_all('a',attrs={'rel':'author'}):
                        author.append(str(x.contents[0]))

                    fandom=[]
                    fandom_tag=li_tag.find('h5',attrs={'class':'fandoms'})
                    for x in fandom_tag.find_all('a',attrs={'class':'tag'}):
                        fandom.append(str(x.contents[0]))

                    warnings=[]
                    for x in li_tag.find_all('li',attrs={'class':'warnings'}):
                        warnings.append(str(x.find('a').contents[0]))
                    relationships=[]
                    for x in li_tag.find_all('li',attrs={'class':'relationships'}):
                        relationships.append(str(x.find('a').contents[0]))
                    characters=[]
                    for x in li_tag.find_all('li',attrs={'class':'characters'}):
                        characters.append(str(x.find('a').contents[0]))
                    freeforms=[]
                    for x in li_tag.find_all('li',attrs={'class':'freeforms'}):
                        freeforms.append(str(x.find('a').contents[0]))

                    chapters=li_tag.find('dd',attrs={'class','chapters'})
                    if chapters.find('a') is not None:
                        chapters.find('a').replaceWithChildren()
                    chapters=''.join(chapters.contents)
                    hits=str(li_tag.find('dd',attrs={'class','hits'}).contents[0])

                    #sometimes the word count is blank
                    words_tag=li_tag.find('dd',attrs={'class','words'})
                    if len(words_tag.contents)==0:
                        words='0'
                    else:
                        words=str(words_tag.contents[0])
                    #for comments/kudos/bookmarks, need to check if the tag exists 
                    comments_tag=li_tag.find('dd',attrs={'class','comments'})
                    if comments_tag is not None:
                        comments=str(comments_tag.contents[0].contents[0])
                    else:
                        comments='0'
                    kudos_tag=li_tag.find('dd',attrs={'class','kudos'})
                    if kudos_tag is not None:
                        kudos=str(kudos_tag.contents[0].contents[0])
                    else:
                        kudos='0'
                    bookmarks_tag=li_tag.find('dd',attrs={'class','bookmarks'})
                    if bookmarks_tag is not None:
                        bookmarks=str(bookmarks_tag.contents[0].contents[0])
                    else:
                        bookmarks='0'

                    pubdate_str=li_tag.find('p',attrs={'class','datetime'}).contents[0]
                    pubdate = datetime.strptime(pubdate_str, '%d %b %Y').date()
                    yield work_id,date,numvisits,title,author,fandom,warnings,relationships,characters,freeforms,words,chapters,comments,kudos,bookmarks,hits,pubdate

                except (KeyError, AttributeError) as e:
                    # A deleted work shows up as
                    #
                    #      <li class="deleted reading work blurb group">
                    #
                    # There's nothing that we can do about that, so just skip
                    # over it.
                    if 'deleted' in li_tag.attrs['class']:
                        self.deleted+=1
                        pass
                    # A locked work shows up with
                    #       <div class="mystery header picture module">
                    elif li_tag.find('div',attrs={'class','mystery'}) is not None:
                        self.deleted+=1
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
