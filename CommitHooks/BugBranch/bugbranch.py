#!python
'''DOCSTRING'''

import ConfigParser
import csv
import pyodbc
import os.path
import re
import svn
import svn.core
import svn.fs
import svn.repos
import sys

# NOTE: Use sys.stderr.write() to pass messages back to the calling process.

# TODO need a PRN project name to SVN branch name mapping to do
# "assigned-to-project" comparisons.

config=ConfigParser.SafeConfigParser()
config.read(os.path.join('F:/','Repositories','ETCM','CommitHooks','BugBranch','bugbranch.ini'))

SVNLOOK = os.path.normpath(config.get('runtime','svnlook'))
DEBUG = os.path.normpath(config.get('runtime','debug'))


# accept multiple arguments, print them all on one line
def write_debug(*args):
    for arg in args:
	sys.stderr.write(arg),
    sys.stderr.write("\n")

class Subversion(object):
    '''DOCSTRING'''
    def __init__(self, repos, txn):
        self.repos = svn.core.svn_path_canonicalize(repos)
	self.fs = svn.repos.svn_repos_fs(svn.repos.svn_repos_open(repos))
        self.txn = svn.fs.svn_fs_open_txn(self.fs, txn)

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
	tmp = svn.fs.svn_fs_txn_prop(self.txn, "svn:author")
	DEBUG and write_debug("[bugbranch] author: ", tmp)
	return tmp

    def __log(self):
        '''Returns the entire SVN log message (private method)'''
	tmp = svn.fs.svn_fs_txn_prop(self.txn, "svn:log")
	DEBUG and write_debug("[bugbranch] log: ", tmp)
	return tmp


class NetResults(object):
    '''DOCSTRING'''
    def __init__(self):
        # fields (and indices) are 'PRN'/0, 'Product'/1, 'Component'/2,
        #   'Title'/3, 'Assigned To'/4, 'Reported By'/5, 'Date Reported'/6,
        #   'Severity'/7, 'Priority'/8, 'Status'/9, 'Resolution'/10,
        #   'Fix Date'/11, 'Reported In Version'/12, 'Assigned to Project'/13
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
            sys.stderr.write('What the deuce?  PRN number not found.\n')
            sys.exit(1)
        elif len(record) > 1:
            sys.stderr.write('Error: found too many PRNs (huh?)')
            sys.exit(1)
        else:
	    DEBUG and write_debug("[bugbranch] record[0].PRN: ", str(record[0].PRN))
	    DEBUG and write_debug("[bugbranch] record[0].Text1: ", str(record[0].Text1))
	    DEBUG and write_debug("[bugbranch] record[0].Assignee: ", str(record[0].Assignee))
	    DEBUG and write_debug("[bugbranch] record[0].Status: ", str(record[0].Status))
            return record[0]

    def name(self, name):
        '''Returns the Subversion name of a NetResults user'''
        section = 'nr2svn'
        ini_file = 'bugbranch.ini'
        try:
            return config.get(section,name)
        # Fatal errors.  Exit immediately.
        except ConfigParser.NoSectionError:
            sys.exit('Error: config file missing section %s (!)' % section)
        except ConfigParser.NoOptionError:
            sys.exit('Error: user %s not found in %s' % (name, ini_file))
        except:
            # only print this if DEBUG
            sys.stderr.write("name: ")
            sys.stderr.write(str(name))
            sys.stderr.write("\n")

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
#    repos = sys.argv[1]
#    txn = sys.argv[2]

    svn = Subversion()
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

