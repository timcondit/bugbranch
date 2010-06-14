#!python
'''DOCSTRING'''

import ConfigParser
import pyodbc
import os.path
import re
import subprocess
import sys
from svn import core, fs, repos

# NOTE: Use sys.stderr.write() to pass messages back to the calling process.

INI_FILE = os.path.join('F:/','Repositories','ETCM.next','CommitHooks','BugBranch','bugbranch.ini')
config = ConfigParser.SafeConfigParser()
config.read(INI_FILE)
SVNLOOK = os.path.normpath(config.get('runtime','svnlook'))
DEBUG = os.path.normpath(config.get('runtime','debug'))


# Accept multiple arguments, print them all on one line.  TODO this needs to be
# in a utilities module somewhere, so it's accessible by all.
def write_debug(*args):
    for arg in args:
        sys.stderr.write(arg),
    sys.stderr.write("\n")

# NOTE: I'm changing the "delivery model" here.  Rather than expose a bunch of
# methods and leave the driver to sort it out, the Subversion class will
# expose one method that will round up all relevant data and return a dict.
class Subversion(object):
    '''DOCSTRING'''
    def __init__(self, repos_path, txn_name):
        # these are for SVNLOOK/changed
        self.rpath = repos_path
        self.tname = txn_name

        self.repos_path = core.svn_path_canonicalize(repos_path)
        self.fs = repos.svn_repos_fs(repos.svn_repos_open(repos_path))
        self.txn = fs.svn_fs_open_txn(self.fs, txn_name)

    def get_details(self):
        '''DOCSTRING'''
        details = {}
        details['prn'] = str(self.__prn()) or None
        details['separator'] = str(self.__separator()) or None
        details['commit_text'] = str(self.__commit_text()) or None
        details['author'] = str(self.__author()) or None
        if details['prn'] != '00000' and details['author'] != 'buildmgr':
            details['branch'] = str(self.__modified_branch()) or None
        else:
            details['branch'] = None
        if DEBUG == "True":
            write_debug("[debug] svn details:", str(details))
        return details

    def __prn(self):
        '''Returns the PRN number from a Subversion transaction, or None'''
        try:
            return self.__commit_re().match(self.__log()).group('prn_number')
        # Fatal error.  Exit immediately.
        except IndexError:
            sys.exit('[prn] Malformed commit message (PRN number missing?)')
        except AttributeError:
            sys.exit("[prn] Where's the commit message?")
        return None

    def __separator(self):
        '''A completely useless method'''
        # If this method causes trouble, delete it.
        try:
            return self.__commit_re().match(self.__log()).group('separator')
        except IndexError:
            sys.exit('[sep] Malformed commit message (separator missing?)')
        except AttributeError:
            sys.exit("[sep] Where's the commit message?")
        return None

    def __commit_text(self):
        '''Returns the commit text from a Subversion transaction, or None'''
        try:
            return self.__commit_re().match(self.__log()).group('commit_text')
        # Fatal error.  Exit immediately.
        except IndexError:
            sys.exit('[commit_text] Malformed commit message (commit text missing?)')
        except AttributeError:
            sys.exit("[commit_text] Where's the commit message?")
        return None

    def __commit_re(self):
        '''Returns a regular expression that matches valid commit messages'''
        # re.MULTILINE may not be appropriate here
        return re.compile(r'''
                (?P<prn_number>^\d{5}\b)    # match five digits at beginning
                                            # of the line (the log message was
                                            # already stripped of whitespace)
                \s*                         # whitespace
                (?P<separator>[:-])         # match the separator character,
                                            # ':' or '-'
                \s*                         # whitespace
                (?P<commit_text>\w+)        # match commit message text
                ''', re.VERBOSE|re.MULTILINE)

    def __author(self):
        '''Returns the author of this transaction'''
        tmp = fs.svn_fs_txn_prop(self.txn, "svn:author")
        if DEBUG == "True":
            write_debug("[author]: ", tmp)
        return tmp


    # Identify the branch based on the path in the transaction.  Returns
    # "Viper", "M.m", "Patch" or None
    #
    # FIXME Two things: simplify the parsing, and identify exactly which
    # strings may be returned.
    #
    # FIXME It's not a modified branch unless the transaction succeeds, so the
    # name is misleading.
    #
    # Examples of matches for the branch:
    # - current project:    \branches\projects\Viper
    # - service packs:      \branches\M.m\maintenance\base
    # - patch branches:     \branches\M.m\maintenance\M.m.SPpn, where pn>00
    def __modified_branch(self):
        '''Returns the branch for this transaction (string)'''
        # paths looks like ['A   path/to/file1.txt\r', 'M   path/to/file2.txt']
        paths = self.__changed().split('\n')
        branch = None

        # First assumption: all changed paths share a common root.  In other
        # words, I won't check that all transactions are from the same branch.
        #
        # Use paths[-1] to get the "longest" path for cases like this:
        # F:\Source\sandbox\branches>svn mkdir 9.10\maintenance\base --parents
        # A         F:\Source\sandbox\branches\9.10
        # A         F:\Source\sandbox\branches\9.10\maintenance
        # A         F:\Source\sandbox\branches\9.10\maintenance\base
        path = ""
        try:
            path = paths[-1]
        # This could happen ... when?  Should be never.
        except IndexError:
            sys.exit("[modbranch] something broke when fetching the path")

        # 'A   path/to/file1.txt\r' --> 'A   path', 'to', 'file1.txt\r'
        path_parts = os.path.normpath(path).split(os.sep)
        if DEBUG == "True":
            write_debug("path_parts:", str(path_parts))

        # ignore the SVN status bits at the front of the path
        if path_parts[0].endswith('branches'):
            if DEBUG == "True":
                write_debug("path_parts[0] endswith branches")
            # continue chewing up the path, left to right
            #
            # Broadly, there are two choices here: projects, or M.m.  This
            # should be moved into a configuration file after I understand it
            # better.
            if path_parts[1] == "projects":
                # Source a list of active projects in bugbranch.ini.
                if path_parts[2] == "Viper":
                    if DEBUG == "True":
                        write_debug("path_parts[2] is ", path_parts[2])
                    return path_parts[2]
                # TODO AFAIK, the only time this would happen is with a new
                # project that the commit hook does not know about.  So rather
                # than just returning it I should flag it as an exception.
                else:
                    # FIXME branch is None here.
                    return branch
            # Wrap in try/catch?
            else:
                major, minor = path_parts[1].split('.')
                try:
                    int(major)
                    int(minor)
                    if DEBUG == "True":
                        write_debug("path_parts[1] is %s.%s" % (major, minor))
                except:
                    write_debug("[modbranch] unknown exception")
                    write_debug("[modbranch] expected branches/MAJOR.MINOR")
                    sys.exit(1)

            # If we get here, it's either a service pack or patch branch.
            # There's a small chance that someone will try to check into one
            # of the old "MAJOR.MINOR/Initial/base" branches, but that's an
            # error and I'm not going to check for it.
            #
            # There's no easy way to distinguish between service packs, for
            # example 10.0.0100 and 10.0.0200.  They both go into the
            # maintenance branch, and it's not profitable to try and tease
            # them apart.
            if path_parts[2] != "maintenance":
                write_debug("[modbranch] unknown exception")
                write_debug("[modbranch] expected branches/MAJOR.MINOR/maintenance")
                sys.exit(1)

            #
            # maintenance branch (service pack)
            #
            if path_parts[3] == "base":
                if DEBUG == "True":
                    write_debug("[bugbranch] returning (int(major), int(minor))")
                return (int(major), int(minor))

            #
            # patch branch
            #
            else:
                if DEBUG == "True":
                    write_debug("path_parts[3]:", path_parts[3])
                try:
                    # Should this be outside the try block?  It's potentially
                    # unreachable otherwise.
                    mjr, mnr, SPpn = path_parts[3].split('.')
                    int(mjr)
                    int(mnr)
                    int(SPpn)
                except:
                    write_debug("[modbranch] unknown exception in modified_branch")
                    write_debug("[modbranch] expected branches/MAJOR.MINOR/maintenance/M.m.SPpn")
                    sys.exit(1)

                # We don't currently allow branch IDs to end in 00, but if we
                # did, it would identify a release branch.  This checks that
                # unlikely scenario.
                patchnum = SPpn[2:]
                if int(patchnum) % 100:
                    # FIXME this is a string.  All branches should be tuples,
                    # even with a single string.
                    branch = "Patch"
                else:
                    sys.exit("It's not a patch branch (and we're out of options)")
        else:
            sys.exit("Error: %s doesn't look like a branch path" % path_parts[0])
        if DEBUG == "True":
            write_debug("branch: %s" % str(branch))
        return branch

    def __changed(self):
        '''Returns the list of files changed in this transaction'''
        p = subprocess.Popen([SVNLOOK, 'changed', self.rpath, '-t', self.tname],
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE)
        stdout_text, stderr_text = p.communicate(None)
        if DEBUG == "True":
            write_debug("[changed] stdout:", stdout_text.strip('\n'))
            write_debug("[changed] stderr:", stderr_text.strip('\n'))
        return stdout_text.strip()

    def __log(self):
        '''Returns the entire SVN log message (private method)'''
        tmp = fs.svn_fs_txn_prop(self.txn, "svn:log")
        if DEBUG == "True":
            write_debug("[log]:", tmp)
        return tmp


class NetResults(object):
    '''DOCSTRING'''
    def __init__(self):
        conn = pyodbc.connect('''
            DRIVER={SQL Server};
            SERVER=CHINOOK;
            DATABASE=ProblemTracker;
            Trusted_Connection=yes''')
        self.cursor = conn.cursor()

    def get_details(self, prn_from_svn):
        '''DOCSTRING'''
        tmp = self.__prn(prn_from_svn)

        details = {}
        details['prn'] = str(tmp.PRN) or None
        details['title'] = str(tmp.Text1) or None
        details['assigned_to'] = str(tmp.Assignee) or None
        details['status'] = str(tmp.Status) or None
        details['project'] = str(tmp.Pulldown8) or None
        if DEBUG == "True":
            write_debug("[bugbranch] NetResults details:", str(details))
        return details

    def __prn(self, prn):
        '''Returns the PRN contents as a list if found, or None'''
        record = self.cursor.execute('''
            SELECT PRN, Text1, Assignee, Status, Pulldown8
            FROM NRTracker.Records
            WHERE PRN = ?
            ''', prn).fetchall()
        if len(record) <= 0:
            sys.exit('Error: PRN number not found.')
        elif len(record) > 1:
            sys.exit('Error: found too many PRNs (huh?)')
        else:
            return record[0]

    def name(self, name):
        '''Returns the Subversion name of a ProblemTracker user'''
        ini_section = 'pt2svn'
        try:
            return config.get(ini_section,name)
        # Fatal errors.  Exit immediately.
        except ConfigParser.NoSectionError:
            sys.exit('Error: config file missing section %s (!)' % ini_section)
        except ConfigParser.NoOptionError:
            sys.exit('Error: user %s not found in %s' % (name, INI_FILE))
        except:
            if DEBUG == "True":
                write_debug("name:", str(name), "\n")
            sys.exit('Error: something broke in NetResults::name()')


if __name__ == '__main__':
    # get SVN data - it's not a commit hook yet, so it uses the last
    # completed transaction (instead of the current one) for testing
    repos = sys.argv[1]
    txn = sys.argv[2]

    # repos, txn come from commit hook (pre-commit.bat)
    svn = Subversion(repos, txn)
    # prn, separator, commit_text, author, branch
    svnd = svn.get_details()

    nr = bugbranch.NetResults()
    # prn, title, assigned_to, status, project
    nrd = nr.get_details(svnd['prn'])

    # make up some NetResults data
    nr_name = nr.name('Tim Condit')
    nrd['prn'] = '21745'

    # do checks
    if svnd['prn'] == nrd['prn']:
        print 'Match: %s == %s' % (svnd['prn'], nrd['prn'])
    else:
        print 'No match: %s != %s' % (svnd['prn'], nrd['prn'])

    if svnd['author'] == nrd['prn']:
        print 'Match: %s == %s' % (svnd['author'], nrd['prn'])
    else:
        print 'No match: %s != %s' % (svnd['author'], nrd['prn'])

    if nrd['prn'] == 'Assigned':
        print 'PRN is assigned (pass)'
    else:
        print 'PRN is NOT assigned (fail)'

