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

# TODO need a PRN project name to SVN branch name mapping to do
# "assigned-to-project" comparisons.

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

class Subversion(object):
    '''DOCSTRING'''
    def __init__(self, repos_path, txn_name):
        # these are for SVNLOOK/changed
        self.rpath = repos_path
        self.tname = txn_name

        self.repos_path = core.svn_path_canonicalize(repos_path)
        self.fs = repos.svn_repos_fs(repos.svn_repos_open(repos_path))
        self.txn = fs.svn_fs_open_txn(self.fs, txn_name)

    def prn(self):
        '''Returns the PRN number from a Subversion transaction, or None'''
        try:
            return self.commit_re().match(self.__log()).group('prn_number')
        # Fatal error.  Exit immediately.
        except IndexError:
            sys.exit('Malformed commit message (PRN number missing?)')
        except AttributeError:
            sys.exit("Where's the commit message?")
        return None

    def separator(self):
        '''A completely useless method'''
        # If this method causes trouble, delete it.
        try:
            return self.commit_re().match(self.__log()).group('separator')
        except IndexError:
            sys.exit('Malformed commit message (separator missing?)')
        except AttributeError:
            sys.exit("Where's the commit message?")
        return None

    def commit_text(self):
        '''Returns the commit text from a Subversion transaction, or None'''
        try:
            return self.commit_re().match(self.__log()).group('commit_text')
        # Fatal error.  Exit immediately.
        except IndexError:
            sys.exit('Malformed commit message (commit text missing?)')
        except AttributeError:
            sys.exit("Where's the commit message?")
        return None

    def commit_re(self):
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

    def author(self):
        '''Returns the author of this transaction'''
        tmp = fs.svn_fs_txn_prop(self.txn, "svn:author")
        if DEBUG is True: write_debug("[bugbranch] author: ", tmp)
        return tmp

    # Try to identify the branch based on the path in the transaction.  It's
    # not a modified branch unless the transaction succeeds, so the name is
    # misleading.  Fix it.
    # Examples of matches for the branch:
    #
    # - current project:    \branches\projects\Viper
    # - service packs:      \branches\M.m\maintenance\base
    # - patch branches:     \branches\M.m\maintenance\M.m.SPpn, where pn>00
    #
    # returns "Viper", M.m, "Engineering Build" or None
    def modified_branch(self):
        '''Returns the branch for this transaction'''
        # paths looks like ['A   path/to/file1.txt\r', 'M   path/to/file2.txt']
        paths = self.changed().split('\n')
        branch = None
#        write_debug('paths[0]:', paths[0])
#        write_debug('paths[-1]:', paths[-1])

        # First assumption: all changed paths share a common root.  In other
        # words, I won't check that all transactions are from the same branch.
#        path = paths[0]
        path = ""
        try:
            path = paths[-1]
        except IndexError:
            write_debug("What the deuce?")
            write_debug("There doesn't seem to be anything in the transaction")
        path_parts = os.path.normpath(path).split(os.sep)
        write_debug("path_parts:", str(path_parts), "\n")

        # DEBUG ignore the SVN status bits at the front of the path
        if path_parts[0].endswith('branches'):
#            write_debug("path_parts[0] endswith branches")
            # continue chewing up the path, left to right
            #
            # Broadly, there are two choices here: projects, or M.m.  This
            # should be moved into a configuration file after I understand it
            # better.
            if path_parts[1] == "projects":
                if path_parts[2] == "Viper":
#                    write_debug("path_parts[1] is Viper")
                    branch = path_parts[2]
                # this should never happen
                else:
                    return branch
            else:
                major, minor = path_parts[1].split('.')
                try:
                    int(major)
                    int(minor)
#                    write_debug("path_parts[1] is %s.%s" % (major, minor))
                except:
                    write_debug("unknown exception in modified_branch")
                    write_debug("expected branches/MAJOR.MINOR")
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
                write_debug("unknown exception in modified_branch")
                write_debug("expected branches/MAJOR.MINOR/maintenance")
                sys.exit(1)

            # FIXME If this particular base branch (or PRN branch for that
            # matter) doesn't exist yet, this check will fail.
            if path_parts[3] == "base":
                # it's a service pack branch
                branch = (major, minor)
            else:
#                write_debug("path_parts[3]:", path_parts[3])
                try:
                    # Should this be outside the try block?  It's potentially
                    # unreachable otherwise.
                    mjr, mnr, SPpn = path_parts[3].split('.')
                    int(mjr)
                    int(mnr)
                    int(SPpn)
                except:
                    write_debug("unknown exception in modified_branch")
                    write_debug("expected branches/MAJOR.MINOR/maintenance/M.m.SPpn")
                    sys.exit(1)
                # This is where I'd check if it's a service pack (ends in 00)
                # or patch branch (ends in something other than 00).  But the
                # SPpn number starts with a leading zero, so it is treated as
                # octal...  Fortunately, I can take advantage of the fact that
                # our patches have to use octal digits for a similar reason.
                #
                pn = SPpn[2:]  # if SPpn isn't a string, we're hosed
                if int(pn) % 100:
                    # it's a patch branch (but we already knew that)
                    branch = "Engineering Build"
                else:
                    write_debug("(1) should never get here")
                    sys.exit(1)
        else:
            sys.exit("Error: %s doesn't look like a branch path" % path_parts[0])
        return branch

    # should this method be private to Subversion?
    def changed(self):
        '''Returns the list of files changed in this transaction'''
        p = subprocess.Popen([SVNLOOK, 'changed', self.rpath, '-t', self.tname],
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE)
        stdout_text, stderr_text = p.communicate(None)
        if DEBUG is True: write_debug("[bugbranch] changed: ", tmp)
        return stdout_text.strip()

    def __log(self):
        '''Returns the entire SVN log message (private method)'''
        tmp = fs.svn_fs_txn_prop(self.txn, "svn:log")
        if DEBUG is True: write_debug("[bugbranch] log: ", tmp)
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

    def prn(self, prn):
        '''Returns the PRN contents as a list if found, or None'''
        record = self.cursor.execute('''
            SELECT PRN, Text1, Assignee, Status, Pulldown8
            FROM NRTracker.Records
            WHERE PRN = ?
            ''', prn).fetchall()
        if len(record) <= 0:
            # should be sys.exit('What the deuce?  PRN number not found.')
            sys.stderr.write('What the deuce?  PRN number not found.')
            sys.exit(1)
        elif len(record) > 1:
            # should be sys.exit('Error: found too many PRNs (huh?)')
            sys.stderr.write('Error: found too many PRNs (huh?)')
            sys.exit(1)
        else:
            if DEBUG is True:
                write_debug("[bugbranch] record[0].PRN: ", str(record[0].PRN))
                write_debug("[bugbranch] record[0].Text1: ", str(record[0].Text1))
                write_debug("[bugbranch] record[0].Assignee: ", str(record[0].Assignee))
                write_debug("[bugbranch] record[0].Status: ", str(record[0].Status))
                write_debug("[bugbranch] record[0].Pulldown8: ", str(record[0].Pulldown8))
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
            if DEBUG is True: write_debug("name: ", str(name), "\n")
            sys.exit('Error: something broke in NetResults::name()')

    def DEBUG_prn_summary(self):
        '''DOCSTRING'''
        self.total=0
        self.assigned=0
        self.closed=0
        self.deferred=0
        self.reported=0
        self.resolved=0
        self.misc=0

        for row in self.nr_prnReader:
            self.total=self.total+1
            if self.total==1:
                continue    # header

            if row[9]=='Assigned':
                self.assigned=self.assigned+1
            elif row[9]=='Closed':
                self.closed=self.closed+1
            elif row[9]=='Deferred':
                self.deferred=self.deferred+1
            elif row[9]=='Reported':
                self.reported=self.reported+1
            elif row[9]=='Resolved':
                self.resolved=self.resolved+1
            else:
                print row[9]
                self.misc=self.misc+1

        # maybe return a dict instead (or throw this all away)
        return '\tAssigned: %s\n\tClosed: %s\n\tDeferred: %s\n' % (
                self.assigned, self.closed, self.deferred )
        return '\tReported: %s\n\tResolved: %s\n\tmisc: %s' % (
                self.reported, self.resolved, self.misc)

#print 'Total bugs: %s' % (total)


if __name__ == '__main__':
    # get SVN data - it's not a commit hook yet, so it uses the last
    # completed transaction (instead of the current one) for testing
    repos = sys.argv[1]
    txn = sys.argv[2]
    svn = Subversion(repos, txn)

    svn_prn = svn.prn()
    svn_separator = svn.separator()
    svn_commit_text = svn.commit_text()
    svn_author = svn.author()

    print 'PRN: %s, separator: %s, commit text: %s' % (svn_prn, svn_separator,
            svn_commit_text)
    print 'SVN author: %s' % svn_author

    # make up some NetResults data
    nr = NetResults()
    nr_name = nr.name('Tim Condit')
    nr_prn = nr.prn('21745')
    #print nr.DEBUG_prn_summary()

    # do checks
    if svn_prn == nr_prn[0]:
        print 'Match: %s == %s' % (svn_prn, nr_prn[0])
    else:
        print 'No match: %s != %s' % (svn_prn, nr_prn[0])

    if svn_author == nr_prn[4]:
        print 'Match: %s == %s' % (svn_author, nr_prn[4])
    else:
        print 'No match: %s != %s' % (svn_author, nr_prn[4])

    if nr_prn[9] == 'Assigned':
        print 'PRN is assigned (pass)'
    else:
        print 'PRN is NOT assigned (fail)'

