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

    svn_separator = svn.separator()
    svn_commit_text = svn.commit_text()
    svn_author = svn.author()
    svn_prn = svn.prn()

    # TESTING
    svn_changed = svn.changed()
#    write_debug(svn_changed, "\n")

    # This is not enough to ensure that only automated commits happen with the
    # buildmgr account.  I can still login as buildmgr as usual and use 00000.
    if svn_prn == '00000' and svn_author == 'buildmgr':
        return

    #if (svn_author != 'timc') and (svn_author != 'anthonyb') and (svn_author != 'dennish'):
    if (svn_author != 'timc') and (svn_author != 'anthonyb'):
        sys.stderr.write("Test users: anthonyb, dennish, timc")
        return
    else:
        nr = bugbranch.NetResults()
        nr_prn = nr.prn(svn_prn)
        # Get the author's full name from NetResults.
        nr_name = nr.name(nr_prn.Assignee)
        if DEBUG is True:
            write_debug("[driver] svn_prn: ", str(svn_prn))
            write_debug("[driver] svn_prn: ", str(svn_prn))

    # do checks
    if nr_prn.Status != 'Assigned':
        if DEBUG is True: write_debug("[driver] nr_prn.Status: ", str(nr_prn.Status))
        sys.exit("Commit failed: PRN%s is not Assigned (it's %s)" % (svn_prn, nr_prn.Status))

    if int(svn_prn) != nr_prn.PRN:
        if DEBUG is True:
            write_debug("[driver] svn_prn: ", str(svn_prn))
            write_debug("[driver] nr_prn.PRN: ", str(nr_prn.PRN))
        sys.exit('Commit failed: invalid PRN number (%s != %s)' % (svn_prn, nr_prn.PRN))

    # TODO it would be nice to use full names here
    if svn_author != nr_name:
        sys.exit('PRN is assigned to %s, not %s' % (nr_name, svn_author))

    # TODO need a check that the user is committing to the right branch.
    else:
        sys.exit("(1) Something's broken in bugbranchdriver.py")

    # use the scrubbed list of projects here
    #
    # If the branch doesn't match the project, you must acquit!


    # TESTING
    svn_branch = svn.modified_branch()
#    write_debug(str(svn_branch), "\n")
    if svn_branch is None:
        sys.exit("(2) project not found - maybe it's new?")
    elif svn_branch == "Viper" and nr_prn.Pulldown8 == "Viper":
        pass
    elif svn_branch == "Engineering Build" and nr_prn.Pulldown8 == "Engineering Build":
        pass
    elif type(svn_branch) == type(tuple):
        if len(svn_branch) == 2:    # major, minor
            mjr, mnr, SPpn = nr_prn.Pulldown8.split('.')
            if svn_branch[0] == mjr and svn_branch[1] == mnr:
                pass
    else:
        sys.exit("(3) Something's broken in bugbranchdriver.py")


if __name__ == '__main__':

    repos = sys.argv[1]
    txn = sys.argv[2]
    checkbug(repos, txn)

