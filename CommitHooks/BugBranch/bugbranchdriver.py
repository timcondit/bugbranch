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
    write_debug("[debug]", str(svnd))

    # This is not enough to ensure that only automated commits happen with the
    # buildmgr account.  I can still login as buildmgr as usual and use 00000.
    if svnd['prn'] == '00000' and svnd['author'] == 'buildmgr':
        return

#    write_debug("[DEBUG] (1) got here\n")
    sys.stderr.write("[DEBUG] (1) got here\n")

    #if (svn_author != 'timc') and (svn_author != 'anthonyb') and (svn_author != 'dennish'):
    if (svnd['author'] != 'timc') and (svnd['author'] != 'anthonyb'):
        sys.stderr.write("Test users: anthonyb, timc")
        return
    else:
        nr = bugbranch.NetResults()
        nr_prn = nr.prn(svnd['prn'])
        # Get the author's full name from NetResults.
        nr_name = nr.name(nr_prn.Assignee)
        if DEBUG is True:
            write_debug("[driver] svn_prn: ", str(svn_prn))
            write_debug("[driver] svn_prn: ", str(svn_prn))

    write_debug("[DEBUG] (2) got here\n")

#    # do checks
#    if nr_prn.Status != 'Assigned':
#        if DEBUG is True: write_debug("[driver] nr_prn.Status: ", str(nr_prn.Status))
#        sys.exit("Commit failed: PRN%s is not Assigned (it's %s)" % (svn_prn, nr_prn.Status))
#
#    write_debug("[DEBUG] (3) got here\n")
#
#    if int(svn_prn) != nr_prn.PRN:
#        if DEBUG is True:
#            write_debug("[driver] svn_prn: ", str(svn_prn))
#            write_debug("[driver] nr_prn.PRN: ", str(nr_prn.PRN))
#        sys.exit('Commit failed: invalid PRN number (%s != %s)' % (svn_prn, nr_prn.PRN))
#
#    write_debug("[DEBUG] (4) got here\n")
#
#    # TODO it would be nice to use full names here
#    if svn_author != nr_name:
#        sys.exit('PRN is assigned to %s, not %s' % (nr_name, svn_author))

    # TODO need a check that the user is committing to the right branch.
#    else:
#        sys.exit("(1) Something's broken in bugbranchdriver.py")

    # use the scrubbed list of projects here
    #
    # If the branch doesn't match the project, you must acquit!

    write_debug("[DEBUG] (5) got here\n")


    # TESTING
    svn_branch = svn.modified_branch()
    write_debug("bugbranchdriver: ", str(svn_branch), "\n")
#    write_debug("bugbranchdriver: ", str(type(svn_branch)), "\n")
    if svn_branch is None:
        sys.exit("(2) project not found - maybe it's new?")
    elif svn_branch == "Viper" and nr_prn.Pulldown8 == "Viper":
        write_debug("(bugbranchdriver): Viper\n")
        pass
    elif svn_branch == "Engineering Build" and nr_prn.Pulldown8 == "Engineering Build":
        write_debug("(bugbranchdriver): Engineering Build\n")
        pass
    elif isinstance(svn_branch, tuple):
        if len(svn_branch) == 2:    # major, minor
            write_debug("(bugbranchdriver) nr_prn.Pulldown8: ", nr_prn.Pulldown8, "\n")
            # Split strings like "10.0.0200 (10.0.SP2)" or "10.1.0000
            # (Viper)", leaving junk behind.  This is complicated by the
            # nearly free-form text in the "Assigned to Project" field.  To
            # get around that problem, split the first part (a proper
            # three-part version OR a project name like "Patch")
            ver, junk = nr_prn.Pulldown8.split()
            if ver == "Patch" or ver == "Engineering": # the first part of "Engineering Build":
                write_debug("[driver] ", ver)
                sys.exit(1)


            # Expect ValueErrors here if the input is not a three-part version
            # number.  The first place this will fail is on projects in
            # "Patch" (formerly "Engineering Build").
            write_debug("[driver] ", ver)
            mjr, mnr, SPpn = ver.split('.')
            write_debug("bugbranchdriver: ", mjr, mnr, SPpn)

            # Success - we're committing to a maintenance branch, and the PRN
            # is for the same major.minor.  Since service packs (.0100, .0200,
            # etc.), are in maintenance branches, this is the only
            # verification available to us.  The PRN provides SPpn, but the
            # branch is no help here.
            if svn_branch[0] == mjr and svn_branch[1] == mnr:
                pass
            else:
                # What?  Error out with details probably.
                write_debug("(bugbranchdriver) you're doing something you shouldn't do (not sure what just yet)")
                pass
    else:
        sys.exit("(3) Something's broken in bugbranchdriver.py")


if __name__ == '__main__':

    repos = sys.argv[1]
    txn = sys.argv[2]
#    sys.exit("[driver] I'm not doing anything")
#    write_debug("[driver] I'm not doing anything")
    checkbug(repos, txn)

