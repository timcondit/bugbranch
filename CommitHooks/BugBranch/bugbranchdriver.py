#!python
'''DOCSTRING'''

# NOTE: Use sys.stderr.write() to pass messages back to the calling process.

import bugbranch
import ConfigParser
import logging
import logging.handlers
import os.path
import sys

BBROOT = os.path.join('F:/','Repositories','ETCM.next','CommitHooks','BugBranch')
INI_FILE = os.path.join(BBROOT, 'bugbranch.ini')
LOG_FILE = os.path.join(BBROOT, 'bugbranch.log')

config = ConfigParser.SafeConfigParser()
config.read(INI_FILE)
DEBUG = os.path.normpath(config.get('runtime','debug'))

# Set up a specific logger with our desired output level
logger = logging.getLogger('Logger')
logger.setLevel(logging.DEBUG)

# Set the format for use by multiple handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Add the log message handler to the logger
loghandler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=8192, backupCount=5)
loghandler.setFormatter(formatter)

logger.addHandler(loghandler)

# move this to bugbranch.ini
smtp_server = 'corpserv04.acme.envisiontelephony.com'
from_addr = 'buildmgr'
to_addr = 'timc'
subject = 'BugBranch activity'

mailhandler = logging.handlers.SMTPHandler(smtp_server, from_addr, to_addr, subject)
mailhandler.setLevel(logging.ERROR)
mailhandler.setFormatter(formatter)

logger.addHandler(mailhandler)


# Accept multiple arguments, print them all on one line.  TODO this needs to be
# in a utilities module somewhere, so it's accessible by all.
def write_debug(*args):
    for arg in args:
        sys.stderr.write(arg),
    sys.stderr.write("\n")

def checkbug(repos, txn):
    '''DOCSTRING'''

    logger.debug("----")

#    write_debug("sys.argv[1]:%s" % sys.argv[1])
#    write_debug("sys.argv[2]:%s" % sys.argv[2])

    # repos, txn come from commit hook (pre-commit.bat)
    svn = bugbranch.Subversion(repos, txn)
    # prn, separator, commit_text, author, branch
    svnd = svn.get_details()

    # DRY
    svnd_p = "SVN details (key, value dump):"
    for key, value in svnd.items():
        svnd_p += ("\n  %s=%s" % (key, value))
    logger.debug(svnd_p)

    # This is not enough to ensure that only automated commits happen with the
    # buildmgr account.  I can still login as buildmgr as usual and use 00000.
    if svnd['prn'] == '00000' and svnd['author'] == 'buildmgr':
        # INFO
        logger.info("svnd['prn'] == '00000' and svnd['author'] == 'buildmgr'")
        return

    if svnd['branch'] == 'developers':
        logger.info("svnd['branch'] == %s" % svnd['branch'])
        return

    nr = bugbranch.NetResults()
    # prn, title, assigned_to, status, project
    nrd = nr.get_details(svnd['prn'])

    # DRY
    nrd_p = "PT details (key, value dump):"
    for key, value in nrd.items():
        nrd_p += ("\n  %s=%s" % (key, value))
    logger.debug(nrd_p)

    authors = ['anthonyb','chrisc','dans','hoangn','jons','timc']
    if svnd['author'] not in authors:
        logger.warning("Test users: %s" % authors)
        return

    # do checks
    if nrd['status'] != 'Assigned':
        msg = "Commit failed: PRN%s is not Assigned (it's %s)" % (svnd['prn'], nrd['status'])
        logger.error(msg)
        sys.exit(msg)

    # This is unlikely to happen.
    if svnd['prn'] != nrd['prn']:
        msg = "Commit failed: invalid PRN number (%s != %s)" % (svnd['prn'], nrd['prn'])
        logger.error(msg)
        sys.exit(msg)

    # convert SVN name to PT name, then compare
    if svnd['author'] != nr.name(nrd['assigned_to']):
        msg = "PRN is assigned to %s, not %s" % (nr.name(nrd['assigned_to']), svnd['author'])
        logger.error(msg)
        sys.exit(msg)

    # short circuit if we're using a Branch PRN to commit to a maintenance or
    # project branch (what about patch branches?)
    if nrd['request_type'] == "Branch":
        write_debug("it's a Branch PRN")
        if svnd['branch'] == "Viper":
            write_debug("it's a Branch PRN (Viper)")
        elif svnd['branch'] == "Patch":
            write_debug("it's a Branch PRN (a patch branch)")
        else:
            try:
                tmp1, tmp2 = svnd['branch'].split(',')
                # DEBUG
                logger.debug("tmp1:%s" % tmp1)
                logger.debug("tmp2:%s" % tmp2)

                # you believe this crap?
                svn_mjr = tmp1.strip(' (')
                svn_mnr = tmp2.strip(' )')
                # if we get here, it's a maintenance branch and we're
                # committing with a branch PRN
                return
            except:
                write_debug("it's a Branch PRN (but I can't identify it)")
    else:
        write_debug("[debug] it's not a Branch PRN")


    # check the project versus the branch path
    if svnd['branch'] is None:
        msg = "SVN branch %s not found in Problem Tracker - maybe it's new?" \
                % (svnd['branch'])
        logger.error(msg)
        sys.exit(msg)
    # FIXME these two if statements are almost identical
    elif svnd['branch'] == "Viper":
        msg = "SVN branch is '%s' and PT project is '%s'" % (svnd['branch'], nrd['project'])
        # FIXME The project name should be cleaned up before we get here.
        if nrd['project'] == "10.1.0000 (Viper)":
            logger.info(msg)
            return
        else:
            logger.error(msg)
            sys.exit(msg)
    # FIXME This will throw a ValueError if svnd['branch'] == "Patch" but
    # nrd['project'] != "Engineering Build"
    #
    # Late note: "Engineering Build" is now "Patch" in PT, so this FIXME is
    # deprecated.  I'll remove it soon.
    # target2: maintenance branches
    elif svnd['branch'] == "Patch":
        msg = "SVN branch is '%s' and PT project is '%s'" % (svnd['branch'], nrd['project'])
        if nrd['project'] == "Patch":
            logger.info(msg)
            return
        # allow branch PRNs to commit merges to multiple branches (2)
        elif nrd['request_type'] == "Branch":
            msg += " // branch PRN"
            logger.info(msg)
            return
        else:
            logger.error(msg)
            sys.exit(msg)

    # BUGBUG if branch is "Viper", but the project is not, it falls thru to
    # here and breaks on the split(',').  Same thing is likely to happen with
    # the patch branches.

    # I'd like to find a better way to do this
    #
    # target3: maintenance or patch branches
    else:
        logger.debug(svnd['branch'])
        # We now have a string disguised as a two-tuple; looks like "(10, 0)".
        # This is where things get ugly (or uglier).
        tmp1, tmp2 = svnd['branch'].split(',')
        # DEBUG
        logger.debug("tmp1:%s" % tmp1)
        logger.debug("tmp2:%s" % tmp2)

        # you believe this crap?
        svn_mjr = tmp1.strip(' (')
        svn_mnr = tmp2.strip(' )')
        # DEBUG
        logger.debug("svn_mjr:%s" % svn_mjr)
        logger.debug("svn_mnr:%s" % svn_mnr)

        # Split strings like "10.0.0200 (10.0.SP2)" or "10.1.0000 (Viper)",
        # leaving junk behind.
        #
        # Caution: this could be just "Patch" (from PT).
        if nrd['project'] == "Patch":
            # (this sucks)
            msg = "Error: SVN branch is '%s' and PT project is '%s'" \
                    % (svnd['branch'], nrd['project'])
            logger.error(msg)
            sys.exit(msg)
        else:
            try:
                pt_ver, junk = nrd['project'].split()
            except ValueError:
                # This would happen if there's a single "word" in the project
                # field.  We shouldn't see this, but if we do, error and exit.
                msg = "Something broke while getting the PT version"
                logger.error(msg)
                sys.exit(msg)

        # Expect ValueErrors here if the input is not a three-part version
        # number.  This would fail on projects in "Patch" (formerly
        # "Engineering Build"), but those should have been caught earlier.
        pt_mjr, pt_mnr, pt_SPpn = pt_ver.split('.')

        # We're committing to a maintenance branch, and the PRN is for the
        # same major.minor.  Since service packs (.0100, .0200, etc.), are in
        # maintenance branches, this is the only verification available to us.
        # The PRN provides SPpn, but the branch is no help here.
        if svn_mjr == pt_mjr and svn_mnr == pt_mnr:
            msg = "svn_mjr == pt_mjr and svn_mnr == pt_mnr (%s==%s, %s==%s)" \
                    % (svn_mjr, pt_mjr, svn_mnr, pt_mnr)
            logger.info(msg)
            return
        # allow branch PRNs to commit merges to multiple branches (3)
        elif nrd['request_type'] == "Branch":
            msg += " // branch PRN"
            logger.info(msg)
            return
        else:
            msg = "Error: it looks like the SVN branch you're committing to\n"
            msg += "  doesn't match up with the 'Assigned to Project' data in\n"
            msg += "  Problem Tracker.  If this is not the case, and something\n"
            msg += "  else is going on, please contact the maintainer.\n\n"
            msg += "This might help:\n"
            msg += "  SVN branch MAJOR.MINOR:%s.%s\n" % (svn_mjr, svn_mnr)
            msg += "  PT project MAJOR.MINOR:%s.%s" % (pt_mjr, pt_mnr)
            write_debug(msg)

            logmsg = "%s.%s != %s.%s (SVN branch != PT project)\n" \
                    % (svn_mjr, svn_mnr, pt_mjr, pt_mnr)
            logger.error(logmsg)
            sys.exit(1)

    # ERROR that should probably be EXCEPTION
    msg = "Unknown condition (contact the maintainer)"
    logger.error(msg)
    logger.error(".. ", svnd_p)
    logger.error(".. ", nrd_p)

if __name__ == '__main__':
    repos = sys.argv[1]
    txn = sys.argv[2]
#    sys.stderr.write('before checkbug()\n')
    checkbug(repos, txn)
#    sys.stderr.write('after checkbug()\n')

