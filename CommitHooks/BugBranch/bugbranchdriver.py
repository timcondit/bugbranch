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

# DRY from bugbranch.py
# accept multiple arguments, print them all on one line
def write_debug(*args):
    for arg in args:
	sys.stderr.write(arg),
    sys.stderr.write("\n")


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


	DEBUG and write_debug("[driver] svn_prn: ", str(svn_prn))
	DEBUG and write_debug("[driver] nr_name: ", str(nr_name))

    # do checks
    if nr_prn.Status != 'Assigned':
	DEBUG and write_debug("[driver] nr_prn.Status: ", str(nr_prn.Status))
        sys.exit("Commit failed: PRN%s is not Assigned (it's %s)" % (svn_prn, nr_prn.Status))

    if int(svn_prn) != nr_prn.PRN:
	DEBUG and write_debug("[driver] svn_prn: ", str(svn_prn))
	DEBUG and write_debug("[driver] nr_prn.PRN: ", str(nr_prn.PRN))
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

