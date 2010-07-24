#
# Copyright (c) 2003 Richard Jones (http://mechanicalcat.net/richard)
# Copyright (c) 2002 ekit.com Inc (http://www.ekit-inc.com/)
# Copyright (c) 2001 Bizar Software Pty Ltd (http://www.bizarsoftware.com.au/)
#
# See the README for full license details.
# 
# $Id: webunittest.py,v 1.12 2004/01/21 22:41:46 richard Exp $

import os, base64, urllib, urlparse, unittest, cStringIO, time, re, sys
import httplib

#try:
#    from M2Crypto import httpslib
#except ImportError:
#    httpslib = None

from SimpleDOM import SimpleDOMParser
from IMGSucker import IMGSucker
from utility import Upload, mimeEncode, boundary, log
import cookie

VERBOSE = os.environ.get('VERBOSE', '')

class HTTPError:
    '''Wraps a HTTP response that is not 200.

    url - the URL that generated the error
    code, message, headers - the information returned by httplib.HTTP.getreply()
    '''
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return 'ERROR: %s'%str(self.response)

class WebFetcher:
    '''Provide a "web client" class that handles fetching web pages.

       Handles basic authentication, HTTPS, detection of error content, ...
       Creates a HTTPResponse object on a valid response.
       Stores cookies received from the server.
    '''

    scheme_handlers = dict(http = httplib.HTTP,
                           https = httplib.HTTPS)
    
    def __init__(self):
        '''Initialise the server, port, authinfo, images and error_content
        attributes.
        '''
        self.protocol = 'http'
        self.server = '127.0.0.1'
        self.port = 80
        self.authinfo = ''
        self.url = None
        self.images = {}
        self.error_content = []
        self.expect_codes = [200, 301, 302]
        self.expect_content = None
        self.expect_cookies = None
        self.accept_cookies = 1
        self.cookies = {}

    result_count = 0

    def clearContext(self):
        self.authinfo = ''
        self.cookies = {}
        self.url = None
        self.images = {}

    def setServer(self, server, port):
        '''Set the server and port number to perform the HTTP requests to.
        '''
        self.server = server
        self.port = int(port)

    #
    # Authentication
    #
    def clearBasicAuth(self):
        '''Clear the current Basic authentication information
        '''
        self.authinfo = ''

    def setBasicAuth(self, username, password):
        '''Set the Basic authentication information to the given username
        and password.
        '''
        self.authinfo = base64.encodestring('%s:%s'%(username,
            password)).strip()

    #
    # cookie handling
    #
    def clearCookies(self):
        '''Clear all currently received cookies
        '''
        self.cookies = {}

    def setAcceptCookies(self, accept=1):
        '''Indicate whether to accept cookies or not
        '''
        self.accept_cookies = accept

    def registerErrorContent(self, content):
        '''Register the given string as content that should be considered a
        test failure (even though the response code is 200).
        '''
        self.error_content.append(content)

    def removeErrorContent(self, content):
        '''Remove the given string from the error content list.
        '''
        self.error_content.remove(content)

    def clearErrorContent(self):
        '''Clear the current list of error content strings.
        '''
        self.error_content = []

    def log(self, message, content):
        '''Log a message to the logfile
        '''
        log(message, content, 'logfile.'+self.server)

    #
    # Register cookies we expect to send to the server
    #
    def registerExpectedCookie(self, cookie):
        '''Register a cookie name that we expect to send to the server.
        '''
        if self.expect_cookies is None:
            self.expect_cookies = [cookie]
            return
        self.expect_cookies.append(cookie)
        self.expect_cookies.sort()

    def removeExpectedCookie(self, cookie):
        '''Remove the given cookie from the list of cookies we expect to
        send to the server.
        '''
        self.expect_cookies.remove(cookie)

    def clearExpectedCookies(self):
        '''Clear the current list of cookies we expect to send to the server.
        '''
        self.expect_cookies = None

    #
    # POST
    #
    def post(self, url, params, code=None, **kw):
        '''Perform a HTTP POST using the specified URL and form parameters.
        '''
        if code is None: code = self.expect_codes
        WebTestCase.result_count = WebTestCase.result_count + 1
        try:
            response = self.fetch(url, params, ok_codes=code, **kw)
        except HTTPError, error:
            self.log('post'+`(url, params)`, error.response.body)
            raise self.failureException, str(error.response)
        return response

    def postAssertCode(self, url, params, code=None, **kw):
        '''Perform a HTTP POST and assert that the return code from the
        server is one of the indicated codes.
        '''
        if code is None: code = self.expect_codes
        WebTestCase.result_count = WebTestCase.result_count + 1
        if type(code) != type([]):
            code = [code]
        try:
            response = self.fetch(url, params, ok_codes = code, **kw)
        except HTTPError, error:
            self.log('postAssertCode'+`(url, params, code)`,
                error.response.body)
            raise self.failureException, str(error.response)
        return response

    def postAssertContent(self, url, params, content, code=None, **kw):
        '''Perform a HTTP POST and assert that the data returned from the
        server contains the indicated content string.
        '''
        if code is None: code = self.expect_codes
        WebTestCase.result_count = WebTestCase.result_count + 1
        if type(code) != type([]):
            code = [code]
        try:
            response = self.fetch(url, params, ok_codes = code, **kw)
        except HTTPError, error:
            self.log('postAssertContent'+`(url, params, code)`,
                error.response.body)
            raise self.failureException, str(error)
        if response.body.find(content) == -1:
            self.log('postAssertContent'+`(url, params, content)`,
                response.body)
            raise self.failureException, 'Expected content not in response'
        return response

    def postAssertNotContent(self, url, params, content, code=None, **kw):
        '''Perform a HTTP POST and assert that the data returned from the
        server doesn't contain the indicated content string.
        '''
        if code is None: code = self.expect_codes
        WebTestCase.result_count = WebTestCase.result_count + 1
        if type(code) != type([]):
            code = [code]
        try:
            response = self.fetch(url, params, ok_codes = code, **kw)
        except HTTPError, error:
            self.log('postAssertNotContent'+`(url, params, code)`,
                error.response.body)
            raise self.failureException, str(error)
        if response.body.find(content) != -1:
            self.log('postAssertNotContent'+`(url, params, content)`,
                response.body)
            raise self.failureException, 'Expected content was in response'
        return response

    def postPage(self, url, params, code=None, **kw):
        '''Perform a HTTP POST using the specified URL and form parameters
        and then retrieve all image and linked stylesheet components for the
        resulting HTML page.
        '''
        if code is None: code = self.expect_codes
        WebTestCase.result_count = WebTestCase.result_count + 1
        try:
            response = self.fetch(url, params, ok_codes=code, **kw)
        except HTTPError, error:
            self.log('postPage %r'%((url, params),), error.response.body)
            raise self.failureException, str(error)

        # Check return code for redirect
        while response.code in (301, 302):
            try:
                # Figure the location - which may be relative
                newurl = response.headers['Location']
                url = urlparse.urljoin(url, newurl)
                response = self.fetch(url, ok_codes=code)
            except HTTPError, error:
                self.log('postPage %r'%url, error.response.body)
                raise self.failureException, str(error)

        # read and parse the content
        page = response.body
        if hasattr(self, 'results') and self.results:
            self.writeResult(url, page)
        try:
            self.pageImages(url, page)
        except HTTPError, error:
            raise self.failureException, str(error)
        return response

    #
    # GET
    #
    def assertCode(self, url, code=None, **kw):
        '''Perform a HTTP GET and assert that the return code from the
        server one of the indicated codes.
        '''
        if code is None: code = self.expect_codes
        return self.postAssertCode(url, None, code=code, **kw)
    get = getAssertCode = assertCode

    def assertContent(self, url, content, code=None, **kw):
        '''Perform a HTTP GET and assert that the data returned from the
        server contains the indicated content string.
        '''
        if code is None: code = self.expect_codes
        return self.postAssertContent(url, None, content, code)
    getAssertContent = assertContent

    def assertNotContent(self, url, content, code=None, **kw):
        '''Perform a HTTP GET and assert that the data returned from the
        server contains the indicated content string.
        '''
        if code is None: code = self.expect_codes
        return self.postAssertNotContent(url, None, content, code)
    getAssertNotContent = assertNotContent

    def page(self, url, code=None, **kw):
        '''Perform a HTTP GET using the specified URL and then retrieve all
        image and linked stylesheet components for the resulting HTML page.
        '''
        if code is None: code = self.expect_codes
        WebTestCase.result_count = WebTestCase.result_count + 1
        return self.postPage(url, None, code=code, **kw)

    def get_base_url(self):
        # try to get a <base> tag and use that to root the URL on
        if hasattr(self, 'getDOM'):
            base = self.getDOM().getByName('base')
            if base:
                # <base href="">
                return base[0].href
        if self.url is not None:
            # join the request URL with the "current" URL
            return self.url
        return None

    #
    # The function that does it all
    #
    def fetch(self, url, postdata=None, server=None, port=None, protocol=None,
                    ok_codes=None):
        '''Run a single test request to the indicated url. Use the POST data
        if supplied.

        Raises failureException if the returned data contains any of the
        strings indicated to be Error Content.
        Returns a HTTPReponse object wrapping the response from the server.
        '''
        # see if the url is fully-qualified (not just a path)
        t_protocol, t_server, t_url, x, t_args, x = urlparse.urlparse(url)
        if t_server:
            protocol = t_protocol
            if ':' in t_server:
                server, port = t_server.split(':')
            else:
                server = t_server
                if protocol == 'http':
                    port = '80'
                else:
                    port = '443'
            url = t_url
            if t_args:
                url = url + '?' + t_args
            # ignore the machine name if the URL is for localhost
            if t_server == 'localhost':
                server = None
        elif not server:
            # no server was specified with this fetch, or in the URL, so
            # see if there's a base URL to use.
            base = self.get_base_url()
            if base:
                t_protocol, t_server, t_url, x, x, x = urlparse.urlparse(base)
                if t_protocol:
                    protocol = t_protocol
                if t_server:
                    server = t_server
                if t_url:
                    url = urlparse.urljoin(t_url, url)

        # TODO: allow override of the server and port from the URL!
        if server is None: server = self.server
        if port is None: port = self.port
        if protocol is None: protocol = self.protocol
        if ok_codes is None: ok_codes = self.expect_codes

        if protocol == 'http':
            handler = self.scheme_handlers.get('http')
            h = handler(server, int(port))

            if int(port) == 80:
               host_header = server
            else: 
               host_header = '%s:%s'%(server, port)
        elif protocol == 'https':
            #if httpslib is None:
                #raise ValueError, "Can't fetch HTTPS: M2Crypto not installed"
            handler = self.scheme_handlers.get('https')
            h = handler(server, int(port))
            
            if int(port) == 443:
               host_header = server
            else: 
               host_header = '%s:%s'%(server, port)
        else:
            raise ValueError, protocol

        params = None
        if postdata:
            for field,value in postdata.items():
                if type(value) == type({}):
                    postdata[field] = []
                    for k,selected in value.items():
                        if selected: postdata[field].append(k)

            # Do a post with the data file
            params = mimeEncode(postdata)
            h.putrequest('POST', url)
            h.putheader('Content-type', 'multipart/form-data; boundary=%s'%
                boundary)
            h.putheader('Content-length', str(len(params)))
        else:
            # Normal GET
            h.putrequest('GET', url)

        # Other Full Request headers
        if self.authinfo:
            h.putheader('Authorization', "Basic %s"%self.authinfo)
        h.putheader('Host', host_header)

        # Send cookies
        #  - check the domain, max-age (seconds), path and secure
        #    (http://www.ietf.org/rfc/rfc2109.txt)
        cookies_used = []
        cookie_list = []
        for domain, cookies in self.cookies.items():
            # check cookie domain
            if not server.endswith(domain):
                continue
            for path, cookies in cookies.items():
                # check that the path matches
                urlpath = urlparse.urlparse(url)[2]
                if not urlpath.startswith(path) and not (path == '/' and
                        urlpath == ''):
                    continue
                for sendcookie in cookies.values():
                    # and that the cookie is or isn't secure
                    if sendcookie['secure'] and protocol != 'https':
                        continue
                    # TODO: check max-age
                    cookie_list.append("%s=%s;"%(sendcookie.key,
                        sendcookie.coded_value))
                    cookies_used.append(sendcookie.key)

        if cookie_list:
            h.putheader('Cookie', ' '.join(cookie_list))

        # check that we sent the cookies we expected to
        if self.expect_cookies is not None:
            assert cookies_used == self.expect_cookies, \
                "Didn't use all cookies (%s expected, %s used)"%(
                self.expect_cookies, cookies_used)

        # finish the headers
        h.endheaders()

        if params is not None:
            h.send(params)

        # handle the reply
        errcode, errmsg, headers = h.getreply()

        # get the body and save it
        f = h.getfile()
        g = cStringIO.StringIO()
        d = f.read()
        while d:
            g.write(d)
            d = f.read()
        response = HTTPResponse(self.cookies, protocol, server, port, url,
            errcode, errmsg, headers, g.getvalue(), self.error_content)
        f.close()

        if errcode not in ok_codes:
            if VERBOSE:
                sys.stdout.write('e')
                sys.stdout.flush()
            raise HTTPError(response)

        # decode the cookies
        if self.accept_cookies:
            try:
                # decode the cookies and update the cookies store
                cookie.decodeCookies(url, server, headers, self.cookies)
            except:
                if VERBOSE:
                    sys.stdout.write('c')
                    sys.stdout.flush()
                raise

        # Check errors
        if self.error_content:
            data = response.body
            for content in self.error_content:
                if data.find(content) != -1:
                    msg = "Matched error: %s"%content
                    if hasattr(self, 'results') and self.results:
                        self.writeError(url, msg)
                    self.log('Matched error'+`(url, content)`, data)
                    if VERBOSE:
                        sys.stdout.write('c')
                        sys.stdout.flush()
                    raise self.failureException, msg

        if VERBOSE:
            sys.stdout.write('_')
            sys.stdout.flush()
        return response

    def pageImages(self, url, page):
        '''Given the HTML page that was loaded from url, grab all the images.
        '''
        sucker = IMGSucker(url, self)
        sucker.feed(page)
        sucker.close()


class WebTestCase(WebFetcher, unittest.TestCase):
    '''Extend the standard unittest TestCase with some HTTP fetching and
    response testing functions.
    '''
    def __init__(self, methodName='runTest'):
        '''Initialise the server, port, authinfo, images and error_content
        attributes.
        '''
        unittest.TestCase.__init__(self, methodName=methodName)
        WebFetcher.__init__(self)


class HTTPResponse(WebFetcher, unittest.TestCase):
    '''Wraps a HTTP response.

    protocol, server, port, url - the request server and URL
    code, message, headers - the information returned by httplib.HTTP.getreply()
    body - the response body returned by httplib.HTTP.getfile()
    '''
    def __init__(self, cookies, protocol, server, port, url, code, message,
            headers, body, error_content=[]):
        WebFetcher.__init__(self)
        # single cookie store per test
        self.cookies = cookies

        self.error_content = error_content[:]

        # this is the request that generated this response
        self.protocol = protocol
        self.server = server
        self.port = port
        self.url = url

        # info about the response
        self.code = code
        self.message = message
        self.headers = headers
        self.body = body
        self.dom = None

    def __str__(self):
        return '%s\nHTTP Response %s: %s'%(self.url, self.code, self.message)

    def getDOM(self):
        '''Get a DOM for this page
        '''
        if self.dom is None:
            parser = SimpleDOMParser()
            try:
                parser.parseString(self.body)
            except:
                log('HTTPResponse.getDOM'+`(self.url, self.code, self.message,
                    self.headers)`, self.body)
                raise
            self.dom = parser.getDOM()
        return self.dom

    def extractForm(self, path=[], include_submit=0, include_button=0):
        '''Extract a form (as a dictionary) from this page.

        The "path" is a list of 2-tuples ('element name', index) to follow
        to find the form. So:
         <html><head>..</head><body>
          <p><form>...</form></p>
          <p><form>...</form></p>
         </body></html>

        To extract the second form, any of these could be used:
         [('html',0), ('body',0), ('p',1), ('form',0)]
         [('form',1)]
         [('p',1)]
        '''
        return self.getDOM().extractElements(path, include_submit,
            include_button)

    def getForm(self, formnum, getmethod, postargs, *args):
        '''Given this page, extract the "formnum"th form from it, fill the
           form with the "postargs" and post back to the server using the
           "postmethod" with additional "args".

           NOTE: the form submission will include any "default" values from
           the form extracted from this page. To "remove" a value from the
           form, just pass a value None for the elementn and it will be
           removed from the form submission.

           example WebTestCase:
             page = self.get('/foo')
             page.getForm(0, self.post, {'name': 'blahblah',
                     'password': 'foo'})

           or the slightly more complex:
             page = self.get('/foo')
             page.getForm(0, self.assertContent, {'name': 'blahblah',
                     'password': None}, 'password incorrect')
        '''
        formData, url = self.getFormData(formnum, postargs)

        # whack on the url params
        l = []
        for k, v in formData.items():
            if isinstance(v, type([])):
                for item in v:
                    l.append('%s=%s'%(urllib.quote(k), 
                        urllib.quote_plus(item, safe='')))
            else:
                l.append('%s=%s'%(urllib.quote(k),
                    urllib.quote_plus(v, safe='')))
        if l:
            url = url + '?' + '&'.join(l)

        # make the post
        return getmethod(url, *args)

    def postForm(self, formnum, postmethod, postargs, *args):
        '''Given this page, extract the "formnum"th form from it, fill the
           form with the "postargs" and post back to the server using the
           "postmethod" with additional "args".

           NOTE: the form submission will include any "default" values from
           the form extracted from this page. To "remove" a value from the
           form, just pass a value None for the elementn and it will be
           removed from the form submission.

           example WebTestCase:
             page = self.get('/foo')
             page.postForm(0, self.post, {'name': 'blahblah',
                     'password': 'foo'})

           or the slightly more complex:
             page = self.get('/foo')
             page.postForm(0, self.postAssertContent, {'name': 'blahblah',
                     'password': None}, 'password incorrect')
        '''
        formData, url = self.getFormData(formnum, postargs)

        # make the post
        return postmethod(url, formData, *args)
  
    def getFormData(self, formnum, postargs={}):
        ''' Postargs are in the same format as the data returned by the
            SimpleDOM extractElements() method, and they are merged with
            the existing form data.
        '''
        dom = self.getDOM()
        form = dom.getByName('form')[formnum]
        formData = form.extractElements()

        # Make sure all the postargs are present in the form:
# TODO this test needs to be switchable, as it barfs when you explicitly
# identify a submit button in the form - the existing form data doesn't
# have submit buttons in it
#        for k in postargs.keys():
#            assert formData.has_key(k), (formData, k)

        formData.update(postargs)
        for k,v in postargs.items():
            if v is None:
                del formData[k]

        # transmogrify select/checkbox/radio select options from dicts
        # (key:'selected') to lists of values
        for k,v in formData.items():
            if isinstance(v, type({})):
                l = []
                for kk,vv in v.items():
                    if vv in ('selected', 'checked'):
                        l.append(kk)
                formData[k] = l
 
        if form.hasattr('action'):
            url = form.action
            base = self.get_base_url()
            if not url or url == '.':
                if base and base[0].hasattr('href'):
                    url = base[0].href
                elif self.url.endswith('/'):
                    url = self.url
                elif self.url.startswith('http') or self.url.startswith('/'):
                    url = '%s/' % '/'.join(self.url.split('/')[:-1])
                else:
                    url = '/%s/' % '/'.join(self.url.split('/')[:-1])

            elif not (url.startswith('/') or url.startswith('http')):
                url = urlparse.urljoin(base, url)
        else:
            url = self.url

        return formData, url

#
# $Log: webunittest.py,v $
# Revision 1.12  2004/01/21 22:41:46  richard
# *** empty log message ***
#
# Revision 1.11  2004/01/20 23:59:39  richard
# *** empty log message ***
#
# Revision 1.10  2003/11/06 06:50:29  richard
# *** empty log message ***
#
# Revision 1.9  2003/11/03 05:11:17  richard
# *** empty log message ***
#
# Revision 1.5  2003/10/08 05:37:32  richard
# fixes
#
# Revision 1.4  2003/08/23 02:01:59  richard
# fixes to cookie sending
#
# Revision 1.3  2003/08/22 00:46:29  richard
# much fixes
#
# Revision 1.2  2003/07/22 01:19:22  richard
# patches
#
# Revision 1.1.1.1  2003/07/22 01:01:44  richard
#
#
# Revision 1.11  2002/02/27 03:00:08  rjones
# more tests, bugfixes
#
# Revision 1.10  2002/02/26 03:14:41  rjones
# more tests
#
# Revision 1.9  2002/02/25 02:58:47  rjones
# *** empty log message ***
#
# Revision 1.8  2002/02/22 06:24:31  rjones
# Code cleanup
#
# Revision 1.7  2002/02/22 04:15:34  rjones
# web test goodness
#
# Revision 1.6  2002/02/13 04:32:50  rjones
# *** empty log message ***
#
# Revision 1.5  2002/02/13 04:24:42  rjones
# *** empty log message ***
#
# Revision 1.4  2002/02/13 02:21:59  rjones
# *** empty log message ***
#
# Revision 1.3  2002/02/13 01:48:23  rjones
# *** empty log message ***
#
# Revision 1.2  2002/02/13 01:16:56  rjones
# *** empty log message ***
#
#
# vim: set filetype=python ts=4 sw=4 et si

