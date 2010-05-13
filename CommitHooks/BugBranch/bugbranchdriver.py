#!python
'''DOCSTRING'''

# NOTE: Use sys.stderr.write() to pass messages back to the calling process.

import bugbranch
import ConfigParser
import os.path
import sys

config=ConfigParser.SafeConfigParser()
config.read(os.path.join('F:/','Repositories','git','ETCM','CommitHooks','BugBranch','bugbranch', 'bugbranch.ini'))

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
        nr_name = nr.name(nr_prn.AssignedTo)

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

