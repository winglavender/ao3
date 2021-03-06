from datetime import datetime
import itertools
import re
import time

from bs4 import BeautifulSoup
import requests

from .works import Work


class User(object):

#   instead of passing plaintext passwords, pass the contents of the _otwarchive_session cookie!
    def __init__(self, username, cookie):
        self.username = username
        sess = requests.Session()
#       previously, used password
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
        jar.set('user_credentials','1',domain='archiveofourown.org') #AO3 requires this cookie to be set
        sess.cookies=jar

        self.sess = sess

        self.deleted = 0 #just for curiosity, count how many times deleted or locked works appear

    def __repr__(self):
        return '%s(username=%r)' % (type(self).__name__, self.username)

    def bookmarks_ids(self, start_page, end_page):
        """
        Returns a list of the user's bookmarks' ids. Ignores external work bookmarks.
        User must be logged in to see private bookmarks.
        """

        api_url = (
            'https://archiveofourown.org/users/%s/bookmarks?page=%%d'
            % self.username)

        bookmarks = []

        if not start_page:
            start_page = 1

        num_works = 0
        for page_no in itertools.count(start=start_page):
            print("Finding page: \t" + str(page_no) + " of bookmarks. \t" + str(num_works) + " bookmarks ids found.")

            req = self.sess.get(api_url % page_no)
            soup = BeautifulSoup(req.text, features='html.parser')

            #if timeout, wait and try again
            while len(req.text) < 20 and "Retry later" in req.text:
                print("timeout... waiting 3 mins and trying again")
                time.sleep(180)
                req = self.sess.get(api_url % page_no)

            # The entries are stored in a list of the form:
            #
            #     <ol class="bookmark index group">
            #       <li id="bookmark_12345" class="bookmark blurb group" role="article">
            #         ...
            #       </li>
            #       <li id="bookmark_67890" class="bookmark blurb group" role="article">
            #         ...
            #       </li>
            #       ...
            #     </o

            ol_tag = soup.find('ol', attrs={'class': 'bookmark'})


            for li_tag in ol_tag.findAll('li', attrs={'class': 'blurb'}):
                num_works = num_works + 1
                try:
                    # <h4 class="heading">
                    #     <a href="/works/12345678">Work Title</a>
                    #     <a href="/users/authorname/pseuds/authorpseud" rel="author">Author Name</a>
                    # </h4>

                    for h4_tag in li_tag.findAll('h4', attrs={'class': 'heading'}):
                        for link in h4_tag.findAll('a'):
                            if ('works' in link.get('href')) and not ('external_works' in link.get('href')):
                                work_id = link.get('href').replace('/works/', '')
                                bookmarks.append(work_id)
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

            # check if this is the last page we want to process
            if end_page and page_no == end_page:
                break
            # The pagination button at the end of the page is of the form
            #
            #     <li class="next" title="next"> ... </li>
            #
            # If there's another page of results, this contains an <a> tag
            # pointing to the next page.  Otherwise, it contains a <span>
            # tag with the 'disabled' class.
            try:
                next_button = soup.find('li', attrs={'class': 'next'})
                if next_button.find('span', attrs={'class': 'disabled'}):
                    break
            except:
                # In case of absence of "next"
                break

        return bookmarks

    def bookmarks(self, start_page=None, end_page=None):
        """
        Returns a list of the user's bookmarks as Work objects.
        Takes forever.
        User must be logged in to see private bookmarks.
        """
        
        # check input
        if start_page and start_page < 1:
            raise IndexError("ERROR: start_page must be 1 or higher")
        if end_page and end_page < 1:
            raise IndexError("ERROR: end_page must be 1 or higher")
        if start_page and end_page and end_page - start_page < 0:
            raise IndexError("ERROR: end_page cannot be before start_page")

        bookmark_total = 0
        bookmark_ids = self.bookmarks_ids(start_page, end_page)
        bookmarks = []

        for bookmark_id in bookmark_ids:
            work = Work(bookmark_id, self.sess)
            bookmarks.append(work)

            bookmark_total = bookmark_total + 1
            # print (str(bookmark_total) + "\t bookmarks found.")

        return bookmarks

    def reading_history(self, tgt_year=None):
        """Returns a list of articles in the user's reading history.

        This requires the user to turn on the Viewing History feature.

        Generates a tuple of work_id,date,numvisits,title,author,fandom,warnings,relationships,characters,freeforms,words,chapters,comments,kudos,bookmarks,hits,pubdate
        Note that the dates are datetime objects, but everything else is either a list of strings (if multiple values) or a string. 

        """
        # TODO: What happens if you don't have this feature enabled?
        # TODO: probably this should be returned as a structured object instead of this giant tuple

        # URL for the user's reading history page
        api_url = (
            'https://archiveofourown.org/users/%s/readings?page=%%d' %
            self.username)

        for page_no in itertools.count(start=1):
            req = self.sess.get(api_url % page_no)
            print("On page: "+str(page_no))
            print("Cumulative deleted works encountered: "+str(self.deleted))
            end_iter = False # check whether we've passed the tgt_year

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
                    curr_year = date.year
                    if tgt_year and curr_year > tgt_year: # skip this item, but we have to check the rest of the page
                        continue 
                    elif tgt_year and curr_year < tgt_year: # we passed tgt_year, stop iterating completely
                        end_iter = True
                        break
                    if "Visited once" in h4_tag.contents[2]:
                        numvisits='1' #TODO: probably want to change these int values to ints instead of strings...
                    else:
                        numvisits=re.search(r'Visited (\d*) times',h4_tag.contents[2]).group(1)

                    #cast all the beautifulsoup navigablestrings to strings
                    title=str(li_tag.find('h4', attrs={'class':'heading'}).find('a').contents[0])

                    author=[] #this is if there's multiple authors
                    author_tag=li_tag.find('h4', attrs={'class':'heading'})
                    for x in author_tag.find_all('a',attrs={'rel':'author'}):
                        author.append(str(x.contents[0]))
                    #TODO: if Anonymous author (no link), should not take the contents, since it'll be blank
                    #Probably something similar to the chapters checker

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

                    #this is longer bc sometimes chapters are a link and sometimes not, so need to normalize
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
                        
                    #for comments/kudos/bookmarks, need to check if the tag exists, bc if there are no comments etc it will not exist
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

            # check if this is the last page we want to process
            if end_iter:
                break

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

    def get_history_csv(self, year=None):
        """ calls reading_history and formats the results into csv rows """
        
        header = ['work_id', 'date', 'numvisits', 'title', 'author', 'fandom', 'warnings', 'relationships', 'characters', 'additional_tags', 'words', 'chapters', 'comments', 'kudos', 'bookmarks', 'hits', 'pubdate']

        rows = []
        for work in self.reading_history(year):
            row = []
            for elem in work:
                if type(elem) is list:
                    row.append(",".join(elem))
                else:
                    row.append(elem)
            rows.append(row)
        return header, rows


