#!python
'''DOCSTRING'''

# NOTE: Use sys.stderr.write() to pass messages back to the calling process.

import bugbranch
import ConfigParser
import os.path
import sys

INI_FILE = os.path.join('F:/','Repositories','ETCM.next','CommitHooks','BugBranch','bugbranch.ini')
config = ConfigParser.SafeConfigParser()
config.read(INI_FILE)
DEBUG = os.path.normpath(config.get('runtime','debug'))

# Accept multiple arguments, print them all on one line.  TODO this needs to be
# in a utilities module somewhere, so it's accessible by all.
def write_debug(*args):
    for arg in args:
        sys.stderr.write(arg),
    sys.stderr.write("\n")


def checkbug(repos, txn):
    # repos, txn come from commit hook (pre-commit.bat)
    svn = bugbranch.Subversion(repos, txn)
    # prn, separator, commit_text, author, branch
    svnd = svn.get_details()

    nr = bugbranch.NetResults()
    # prn, title, assigned_to, status, project
    nrd = nr.get_details(svnd['prn'])

    # This is not enough to ensure that only automated commits happen with the
    # buildmgr account.  I can still login as buildmgr as usual and use 00000.
    if svnd['prn'] == '00000' and svnd['author'] == 'buildmgr':
        return

    if (svnd['author'] != 'timc') and (svnd['author'] != 'anthonyb'):
        write_debug("Test users: anthonyb, timc")
        return

    # do checks
    if nrd['status'] != 'Assigned':
        sys.exit("Commit failed: PRN%s is not Assigned (it's %s)" % (svnd['prn'], nrd['status']))

    # Does this still need int()?  And what's the point anyway?  Maybe a case
    # where a PRN is assigned to someone else?  That's handled elsewhere.
    if int(svnd['prn']) != nrd['prn']:
        sys.exit('Commit failed: invalid PRN number (%s != %s)' % (svnd['prn'], nrd['prn']))

    # it would be nice to use full names here
    if svnd['author'] != nrd['assigned_to']:
        sys.exit('PRN is assigned to %s, not %s' % (nrd['assigned_to'], svnd['author']))

    # check the project versus the branch path
    if svnd['branch'] is None:
        sys.exit("[driver] project not found - maybe it's new?")
    elif svnd['branch'] == "Viper" and nrd['project'] == "Viper":
        pass
    elif svnd['branch'] == "Patch" and nrd['project'] == "Engineering Build":
#        write_debug("[driver]: Patch (Engineering Build)\n")
        pass
    elif isinstance(svnd['branch'], tuple):
        if len(svnd['branch']) == 2:    # major, minor
            write_debug("nrd['project']:", nrd['project'])
            # Split strings like "10.0.0200 (10.0.SP2)" or "10.1.0000
            # (Viper)", leaving junk behind.
            ver, junk = nrd['project'].split()

            # Expect ValueErrors here if the input is not a three-part version
            # number.  This would fail on projects in "Patch" (formerly
            # "Engineering Build"), but those should have been caught earlier.
#            write_debug("[driver] ver:", ver)
            mjr, mnr, SPpn = ver.split('.')
#            write_debug("[driver] mjr, mnr, SPpn:", mjr, mnr, SPpn)

            # We're committing to a maintenance branch, and the PRN is for the
            # same major.minor.  Since service packs (.0100, .0200, etc.), are
            # in maintenance branches, this is the only verification available
            # to us.  The PRN provides SPpn, but the branch is no help here.
            if svnd['branch'][0] == mjr and svnd['branch'][1] == mnr:
                pass
            else:
                # What?  Error out with details probably.
                write_debug("[2] Something's broken in bugbranchdriver.py")
                pass
    else:
        write_debug("[3] Something's broken in bugbranchdriver.py")


if __name__ == '__main__':
    repos = sys.argv[1]
    txn = sys.argv[2]
    checkbug(repos, txn)

