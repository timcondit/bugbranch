<<<<<<< HEAD
#!python
'''DOCSTRING'''

# NOTE: Use sys.stderr.write() to pass messages back to the calling process.

import bugbranch
import ConfigParser
import os.path
import sys

config=ConfigParser.SafeConfigParser()
config.read(os.path.join('F:/','Repositories','ETCM','CommitHooks','BugBranch','bugbranch.ini'))

DEBUG = os.path.normpath(config.get('runtime','debug'))

def checkbug(repos, txn):
    # repos, txn come from commit hook (pre-commit.bat)
    svn = bugbranch.Subversion(repos, txn)

    svn_separator = svn.separator()
    svn_commit_text = svn.commit_text()
    svn_author = svn.author()
    svn_prn = svn.prn()
    # This is not enough to ensure that only automated commits happen with the
    # buildmgr account.  I can still login as buildmgr as usual and use 00000.
    if svn_prn == '00000' and svn_author == 'buildmgr':
        return
#        sys.exit("Error: '%s/%s' should only be used for automated commits!" %
#                (svn_prn, svn_author))

    #if (svn_author != 'timc') and (svn_author != 'anthonyb') and (svn_author != 'dennish'):
    if (svn_author != 'timc') and (svn_author != 'anthonyb'):
	sys.stderr.write("Test users: anthonyb, dennish, timc")
        return
    else:
        nr = bugbranch.NetResults()
        nr_prn = nr.prn(svn_prn)
        # Get the author's full name from NetResults.  For now, at least, that
        # means fetching by index.
        nr_name = nr.name(nr_prn.Assignee)

	if DEBUG is True:
	    # only print this if DEBUG
	    sys.stderr.write("[bugbranchdriver.py] svn_prn: ")
	    sys.stderr.write(str(svn_prn))
	    sys.stderr.write("\n")
	    sys.stderr.write("[bugbranchdriver.py] nr_name: ")
	    sys.stderr.write(str(nr_name))
	    sys.stderr.write("\n")

    # do checks
    if nr_prn.Status != 'Assigned':
	if DEBUG is True:
	    sys.stderr.write("[bugbranchdriver.py] nr_prn.Status: ")
	    sys.stderr.write(str(nr_prn.Status))
	    sys.stderr.write("\n")
	sys.exit("Commit failed: PRN%s is not Assigned (it's %s)" % (svn_prn, nr_prn.Status))

    if int(svn_prn) != nr_prn.PRN:
	if DEBUG is True:
	    sys.stderr.write("[bugbranchdriver.py] svn_prn: ")
	    sys.stderr.write(svn_prn)
	    sys.stderr.write("\n")
	    sys.stderr.write("[bugbranchdriver.py] nr_prn.PRN: ")
	    sys.stderr.write(str(nr_prn.PRN))
	    sys.stderr.write("\n")
        sys.exit('Commit failed: invalid PRN number (%s != %s)' % (
            svn_prn, nr_prn.PRN))

    # TODO it would be nice to use full names here
    if svn_author != nr_name:
        sys.exit('PRN is assigned to %s, not %s' % (nr_name, svn_author))

    # TODO need a check that the user is committing to the right branch.
    else:
        print "Something's broken!"

if __name__ == '__main__':
    repos = sys.argv[1]
    txn = sys.argv[2]
    checkbug(repos, txn)

=======
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
    elif svnd['branch'] == "Viper" and nrd['project'] == "10.1.0000":
        return
    elif svnd['branch'] == "Patch" and nrd['project'] == "Engineering Build":
#        write_debug("[driver]: Patch (Engineering Build)\n")
        return
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
                return
            else:
                # What?  Error out with details probably.
                sys.exit("[2] Something's broken in bugbranchdriver.py")
    else:
        sys.exit("[3] Something's broken in bugbranchdriver.py")


if __name__ == '__main__':
    repos = sys.argv[1]
    txn = sys.argv[2]
    checkbug(repos, txn)

>>>>>>> 51d6138355786e5ea4d5344c1136123ec1c3d3cb
