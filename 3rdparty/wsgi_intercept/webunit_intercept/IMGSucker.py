#
# Copyright (c) 2003 Richard Jones (http://mechanicalcat.net/richard)
# Copyright (c) 2002 ekit.com Inc (http://www.ekit-inc.com/)
# Copyright (c) 2001 Bizar Software Pty Ltd (http://www.bizarsoftware.com.au/)
#
# See the README for full license details.
# 
# $Id: IMGSucker.py,v 1.2 2003/07/22 01:19:22 richard Exp $

import htmllib, formatter, urlparse

class IMGSucker(htmllib.HTMLParser):
    '''Suck in all the images and linked stylesheets for an HTML page.

    The sucker uses a HTTP session object which provides:
         url - the URL of the page that we're parsing
     session - a HTTP session object which provides:
               fetch: a method that retrieves a file from a URL
               images: a mapping that holds the fetched images
     
    Once instantiated, the sucker is fed data through its feed method and
    then it must be close()'ed.

    **CURRENTLY NOT IMPLEMENTED**
    Once done, the output attribute of the sucker holds the HTML with URLs
    rewritten for local files where appropriate.
    **CURRENTLY NOT IMPLEMENTED**
    '''
    def __init__(self, url, session):
        htmllib.HTMLParser.__init__(self, formatter.NullFormatter())
        self.base = url
        self.session = session
        self.output = ""

    def handle_data(self, data):
        self.output = self.output + data

    def unknown_starttag(self, tag, attributes):
        self.output = self.output + '<%s' % tag
        for name, value in attributes:
            self.output = self.output + ' %s="%s"' % (name, value)
        self.output = self.output + '>'

    def handle_starttag(self, tag, method, attributes):
        if tag == 'img' or tag == 'base' or tag == 'link':
            method(attributes)
        else:
            self.unknown_starttag(tag, attributes)

    def unknown_endtag(self, tag):
        self.output = self.output + '</%s>' % tag
    
    def handle_endtag(self, tag, method):
        self.unknown_endtag(tag)

    def close(self):
        htmllib.HTMLParser.close(self)

    def do_base(self, attributes):
        for name, value in attributes:
            if name == 'href':
                self.base = value
        # Write revised base tag to file
        self.unknown_starttag('base', attributes)

    def do_img(self, attributes):
        newattributes = []
        for name, value in attributes:
            if name == 'src':
                url = urlparse.urljoin(self.base, value)
                # TODO: figure the re-write path
                # newattributes.append((name, path))
                if not self.session.images.has_key(url):
                    self.session.images[url] = self.session.fetch(url)
            else:
                newattributes.append((name, value))
        # Write the img tag to file (with revised paths)
        self.unknown_starttag('img', newattributes)

    def do_link(self, attributes):
        newattributes = [('rel', 'stylesheet'), ('type', 'text/css')]
        for name, value in attributes:
            if name == 'href':
                url = urlparse.urljoin(self.base, value)
                # TODO: figure the re-write path
                # newattributes.append((name, path))
                self.session.fetch(url)
            else:
                newattributes.append((name, value))
        # Write the link tag to file (with revised paths)
        self.unknown_starttag('link', newattributes)

#
# $Log: IMGSucker.py,v $
# Revision 1.2  2003/07/22 01:19:22  richard
# patches
#
# Revision 1.1.1.1  2003/07/22 01:01:44  richard
#
#
# Revision 1.4  2002/02/27 03:00:08  rjones
# more tests, bugfixes
#
# Revision 1.3  2002/02/25 03:11:00  rjones
# *** empty log message ***
#
# Revision 1.2  2002/02/13 01:16:56  rjones
# *** empty log message ***
#
#
# vim: set filetype=python ts=4 sw=4 et si

