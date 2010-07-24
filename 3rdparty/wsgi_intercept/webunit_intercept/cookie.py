import re, urlparse, Cookie

class Error:
    '''Handles a specific cookie error.

    message - a specific message as to why the cookie is erroneous
    '''
    def __init__(self, message):
        self.message = str(message)

    def __str__(self):
        return 'COOKIE ERROR: %s'%self.message

def parse_cookie(text, qparmre=re.compile(
        r'([\0- ]*([^\0- ;,=\"]+)="([^"]*)\"([\0- ]*[;,])?[\0- ]*)'),
        parmre=re.compile(
        r'([\0- ]*([^\0- ;,=\"]+)=([^\0- ;,\"]*)([\0- ]*[;,])?[\0- ]*)')):
    result = {}
    l = 0
    while 1:
        if qparmre.match(text[l:]) >= 0:
            # Match quoted correct cookies
            name=qparmre.group(2)
            value=qparmre.group(3)
            l=len(qparmre.group(1))
        elif parmre.match(text[l:]) >= 0:
            # Match evil MSIE cookies ;)
            name=parmre.group(2)
            value=parmre.group(3)
            l=len(parmre.group(1))
        else:
            # this may be an invalid cookie.
            # We'll simply bail without raising an error
            # if the cookie is invalid.
            return result
        if not result.has_key(name):
            result[name]=value
    return result

def decodeCookies(url, server, headers, cookies):
    '''Decode cookies into the supplied cookies dictionary
       http://www.ietf.org/rfc/rfc2109.txt
    '''
    # the path of the request URL up to, but not including, the right-most /
    request_path = urlparse.urlparse(url)[2]
    if len(request_path) > 1 and request_path[-1] == '/':
        request_path = request_path[:-1]

    hdrcookies = Cookie.SimpleCookie("\n".join(map(lambda x: x.strip(), 
        headers.getallmatchingheaders('set-cookie'))))
    for cookie in hdrcookies.values():
        # XXX: there doesn't seem to be a way to determine if the
        # cookie was set or defaulted to an empty string :(
        if cookie['domain']:
            domain = cookie['domain']

            # reject if The value for the Domain attribute contains no
            # embedded dots or does not start with a dot.
            if '.' not in domain:
                raise Error, 'Cookie domain "%s" has no "."'%domain
            if domain[0] != '.':
                raise Error, 'Cookie domain "%s" doesn\'t start '\
                    'with "."'%domain
            # reject if The value for the request-host does not
            # domain-match the Domain attribute.
            if not server.endswith(domain):
                raise Error, 'Cookie domain "%s" doesn\'t match '\
                    'request host "%s"'%(domain, server)
            # reject if The request-host is a FQDN (not IP address) and
            # has the form HD, where D is the value of the Domain
            # attribute, and H is a string that contains one or more dots.
            if re.search(r'[a-zA-Z]', server):
                H = server[:-len(domain)]
                if '.' in H:
                    raise Error, 'Cookie domain "%s" too short '\
                    'for request host "%s"'%(domain, server)
        else:
            domain = server

        # path check
        path = cookie['path'] or request_path
        # reject if Path attribute is not a prefix of the request-URI
        # (noting that empty request path and '/' are often synonymous, yay)
        if not (request_path.startswith(path) or (request_path == '' and
                cookie['path'] == '/')):
            raise Error, 'Cookie path "%s" doesn\'t match '\
                'request url "%s"'%(path, request_path)

        bydom = cookies.setdefault(domain, {})
        bypath = bydom.setdefault(path, {})
        bypath[cookie.key] = cookie

