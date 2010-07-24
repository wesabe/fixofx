"""
A zope.testbrowser-style Web browser interface that redirects specified
connections to a WSGI application.
"""

from mechanize import Browser as MechanizeBrowser
from wsgi_intercept.mechanize_intercept import Browser as InterceptBrowser
from zope.testbrowser.browser import Browser as ZopeTestbrowser
from httplib import HTTP
import sys, os.path        

class WSGI_Browser(ZopeTestbrowser):
    """
    Override the zope.testbrowser.browser.Browser interface so that it
    uses PatchedMechanizeBrowser 
    """
    
    def __init__(self, *args, **kwargs):
        kwargs['mech_browser'] = InterceptBrowser()
        ZopeTestbrowser.__init__(self, *args, **kwargs)
