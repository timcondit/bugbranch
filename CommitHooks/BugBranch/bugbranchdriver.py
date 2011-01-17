#!python
'''DOCSTRING'''

# NOTE: Use sys.stderr.write() to pass messages back to the calling process.

import bugbranch
from bugbranch import write_debug
import ConfigParser
import logging
import logging.handlers
import os.path
import sys

BBROOT = r'F:/Repositories/ETCM/CommitHooks/BugBranch'
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


def checkbug(repos, txn):
    '''DOCSTRING'''

    logger.debug("----")

    # repos, txn come from commit hook (pre-commit.bat)
    svn = bugbranch.Subversion(repos, txn)

    # prn, separator, commit_text, author, branch
    svnd = svn.get_details()

    # DRY
    svnd_p = "SVN details (key, value dump):"
    for key, value in svnd.items():
        svnd_p += ("\n  %s=%s" % (key, value))
    logger.debug(svnd_p)

    # There's no PRN00000 and the query will fail, so check this one before
    # fetching the PRN data.
    if svnd['prn'] == '00000' and svnd['author'] == 'buildmgr':
        logger.info("svnd['prn'] == '00000' and svnd['author'] == 'buildmgr'")
        return

    nr = bugbranch.NetResults()
    # prn, title, assigned_to, status, project
    nrd = nr.get_details(svnd['prn'])

    # DRY
    nrd_p = "PT details (key, value dump):"
    for key, value in nrd.items():
        nrd_p += ("\n  %s=%s" % (key, value))
    logger.debug(nrd_p)

    # do checks
    try:
        if svnd['branch'][0] is None:
            msg = "0100: Commit failed: branch probably not in active list"
            logger.error(msg)
            sys.exit(msg)
    except TypeError:
        msg = "0100: Commit failed: branch probably not in active list"
        logger.error(msg)
        sys.exit(msg)
    # if we hit this, may need to update the list of projects
    if nrd['project'][0] is None:
        msg = "0100: Commit failed: project not found in active list"
        logger.error(msg)
        sys.exit(msg)
#    # this is redundant
#    if nrd['project'][1] == 'no_project' or nrd['project'][1] == 'backlog':
#        msg = "0110: Commit failed: PRN%s is marked '%s'" % (svnd['prn'], nrd['project'][0])
#        logger.error(msg)
#        sys.exit(msg)
    if nrd['status'] != 'Assigned':
        msg = "0120: Commit failed: PRN%s is not Assigned (it's %s)" % (svnd['prn'], nrd['status'])
        logger.error(msg)
        sys.exit(msg)
    if svnd['prn'] != nrd['prn']:
        msg = "0130: Commit failed: invalid PRN number (%s != %s)" % (svnd['prn'], nrd['prn'])
        logger.error(msg)
        sys.exit(msg)
    # convert SVN name to PT name, then compare
    if svnd['author'] != nr.name(nrd['assigned_to']):
        msg = "0140: PRN is assigned to %s, not %s" % (nr.name(nrd['assigned_to']), svnd['author'])
        logger.error(msg)
        sys.exit(msg)
#    if nrd['project'][1] == '10_1_0000' and svnd['branch'][0] == 'Viper':
#        # TMP exception for PRN23870, part 1 of 2 - timc 1/3/2010
#        if svnd['author'] == 'michaelw' or svnd['author'] == 'dennish':
#            msg = "[driver] NRD '%s', SVN '%s'" % (nrd['project'][0], svnd['branch'][0])
#            write_debug(msg)
#            logger.info(msg)
#            write_debug(svnd['revision'])
#            nr.update_record(svnd['prn'], svnd['author'], svnd['commit_text'],
#                    svnd['revision'], svnd['branch'][1], svn.modified_files())
#            return
#        else:
#            msg = "0150: The Viper project is closed in ProblemTracker.  To\n"
#            msg += "check into the Viper branch, mark the bug as project 10.1 GA"
#            logger.error(msg)
#            sys.exit(msg)
#
#    if nrd['project'][1] == '10_0_m' and svnd['branch'][0] == '10_0_0115':
#        msg = "0160: There should be no more check-ins on this branch"
#        logger.error(msg)
#        sys.exit(msg)
#    if nrd['project'][1] == 'patch':
#        pass

    # Notes:
    #
    # 1: I'm not going to bother with nrd['request_type'] for now.  Maybe
    #    later.  It was in there before, but I don't see the benefit.
    # 2: A decision table would be nice here.
    # 3: Consider adding 9.7/maintenance/base and 9.7/SP1/EB/AFB-HPX

            #(nrd['project'][1] == '10_2_0000'   and svnd['branch'][0] == 'Charlie')  or \
    if      (nrd['project'][1] == '10_2_0000'   and svnd['branch'][0] == 'AvayaPDS')  or \
            (nrd['project'][1] == '10_2_0000'   and svnd['branch'][0] == 'JTAPI')     or \
            (nrd['project'][1] == '10_1_0001'   and svnd['branch'][0] == 'Viper')     or \
            (nrd['project'][1] == '10_0_m'      and svnd['branch'][0] == '10_0_m')    or \
            (nrd['project'][1] == '10_0_m'      and svnd['branch'][0] == '10_0_0216') or \
            (nrd['project'][1] == '10_0_m'      and svnd['branch'][0] == '10_0_0217') or \
            (nrd['project'][1] == '10_0_m'      and svnd['branch'][0] == '10_0_0220') or \
            (nrd['project'][1] == '9_7__9_10_m' and svnd['branch'][0] == '9_10_m'):

        msg = "[driver] NRD '%s', SVN '%s'" % (nrd['project'][0], svnd['branch'][0])
        write_debug(msg)
        logger.info(msg)
        write_debug(svnd['revision'])
        nr.update_record(svnd['prn'], svnd['author'], svnd['commit_text'],
                svnd['revision'], svnd['branch'][1], svn.modified_files())
        return
    else:
        msg = "commit blocked: NRD '%s', SVN '%s', [PRN%s]" % \
                (nrd['project'][0], svnd['branch'][0], svnd['prn'])
        logger.error(msg)
        sys.exit(msg)

if __name__ == '__main__':
    repos = sys.argv[1]
    txn = sys.argv[2]
    checkbug(repos, txn)

