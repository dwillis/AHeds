#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api.urlfetch import fetch
import StringIO
from BeautifulSoup import BeautifulSoup

class FeedItem(db.Model):
    title = db.StringProperty()
    description = db.StringProperty(multiline=True)
    url = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)



class MainHandler(webapp.RequestHandler):
    def get(self):
        title = "WSJ A-Heds"
        link = "http://online.wsj.com/public/page/page-one-ahed.html"
        description = "The latest A-Heds from the Wall Street Journal"
        
        rss="""<?xml version="1.0" encoding="ISO-8859-1"?>
            <rss version="2.0">
                <channel>
                    <title>""" + title + """</title>
                    <link>"""+ link + """</link>
                    <description>""" +  description + """"</description>
                    <language>en-us</language>
            """        
        items = db.GqlQuery("SELECT * FROM FeedItem ORDER BY date DESC LIMIT 20")
        for item in items:
            rss+="""
                    <item>
                        <title>%s</title>
                        <link>%s</link>
                        <description>%s</description>
                        <pubDate>%s</pubDate>
                    </item>\n""" % (item.title, item.url, item.description, item.date)
        rss+="""
                </channel>
            </rss>
            """
        self.response.out.write(rss)
        
        
class Feeder(webapp.RequestHandler):
    def get(self):
        url = "http://online.wsj.com/public/page/page-one-ahed.html"
        content = fetch(url).content
        soup = BeautifulSoup(content)
        current_item = soup.find('ul', { "class" : "newsItem" })
        stories = FeedItem.all()
        previous_items = soup.findAll('li', { "class" : "ahed_listitem" })
        for item in previous_items:
            stories = FeedItem.all()
            story = stories.filter('url =', item.find('a')["href"]).get()
            if not story:
                feed_item = FeedItem(url=item.find('a')["href"], title=str(item.find('h2').find('a').string.strip()), description=str(item.find('p').string))
                feed_item.put()
        current_story = stories.filter('url =', current_item.find('a')["href"]).get()
        if not current_story:
            feed_item = FeedItem(url="http://online.wsj.com" + current_item.findAll('div')[3].find('a')["href"], title=str(current_item.find('h1').find('a').string.strip()), description=str(current_item.find('p').string))
            feed_item.put()        
        self.redirect('/')
            
        

def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/_update', Feeder)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
