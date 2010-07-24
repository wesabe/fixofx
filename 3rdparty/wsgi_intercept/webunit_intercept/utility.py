#
# Copyright (c) 2003 Richard Jones (http://mechanicalcat.net/richard)
# Copyright (c) 2002 ekit.com Inc (http://www.ekit-inc.com/)
# Copyright (c) 2001 Bizar Software Pty Ltd (http://www.bizarsoftware.com.au/)
#
# See the README for full license details.
# 
# $Id: utility.py,v 1.3 2003/08/23 02:01:59 richard Exp $

import cStringIO
import os.path

class Upload:
    '''Simple "sentinel" class that lets us identify file uploads in POST
    data mappings.
    '''
    def __init__(self, filename):
        self.filename = filename
    def __cmp__(self, other):
        return cmp(self.filename, other.filename)

boundary = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
sep_boundary = '\n--' + boundary
end_boundary = sep_boundary + '--'

def mimeEncode(data, sep_boundary=sep_boundary, end_boundary=end_boundary):
    '''Take the mapping of data and construct the body of a
    multipart/form-data message with it using the indicated boundaries.
    '''
    ret = cStringIO.StringIO()
    for key, value in data.items():
        if not key:
            continue
        # handle multiple entries for the same name
        if type(value) != type([]): value = [value]
        for value in value:
            ret.write(sep_boundary)
            # if key starts with a '$' then the entry is a file upload
            if isinstance(value, Upload):
                ret.write('\nContent-Disposition: form-data; name="%s"'%key)
                ret.write('; filename="%s"\n\n'%value.filename)
                if value.filename:
                    value = open(os.path.join(value.filename), "rb").read()
                else:
                    value = ''
            else:
                ret.write('\nContent-Disposition: form-data; name="%s"'%key)
                ret.write("\n\n")
            ret.write(str(value))
            if value and value[-1] == '\r':
                ret.write('\n')  # write an extra newline
    ret.write(end_boundary)
    return ret.getvalue()

def log(message, content, logfile='logfile'):
    '''Log a single message to the indicated logfile
    '''
    logfile = open(logfile, 'a')
    logfile.write('\n>>> %s\n'%message)
    logfile.write(str(content) + '\n')
    logfile.close()

#
# $Log: utility.py,v $
# Revision 1.3  2003/08/23 02:01:59  richard
# fixes to cookie sending
#
# Revision 1.2  2003/07/22 01:19:22  richard
# patches
#
# Revision 1.1.1.1  2003/07/22 01:01:44  richard
#
#
# Revision 1.4  2002/02/25 02:59:09  rjones
# *** empty log message ***
#
# Revision 1.3  2002/02/22 06:24:31  rjones
# Code cleanup
#
# Revision 1.2  2002/02/13 01:16:56  rjones
# *** empty log message ***
#
#
# vim: set filetype=python ts=4 sw=4 et si

