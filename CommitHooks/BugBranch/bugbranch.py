#!python
'''DOCSTRING'''

import ConfigParser
import pyodbc
import os.path
import re
import subprocess
import sys
from svn import core, fs, repos #delta
from time import strftime

# NOTE: Use sys.stderr.write() to pass messages back to the calling process.

config = ConfigParser.SafeConfigParser()
config.read(r'F:/Repositories/newbugbranch/CommitHooks/BugBranch/bugbranch.ini')
SVNLOOK = os.path.normpath(config.get('runtime','svnlook'))
DEBUG = os.path.normpath(config.get('runtime','debug'))


# Accept multiple arguments, print them all on one line.
def write_debug(*args):
    for arg in args:
        sys.stderr.write(arg),
    sys.stderr.write("\n")

# The Subversion class exposes one method that will round up all relevant data
# and return a dict.
class Subversion(object):
    '''DOCSTRING'''
    def __init__(self, repos_path, txn_name):
        # these are for SVNLOOK/changed
        self.rpath = repos_path
        self.tname = txn_name

        self.repos_path = core.svn_path_canonicalize(repos_path)
        self.fs = repos.svn_repos_fs(repos.svn_repos_open(repos_path))
        self.txn = fs.svn_fs_open_txn(self.fs, txn_name)
        self.txn_root = fs.svn_fs_txn_root(self.txn)

    def get_details(self):
        '''DOCSTRING'''
        details = {}
        details['prn'] = str(self.__prn()) or None
        details['separator'] = str(self.__separator()) or None
        details['commit_text'] = str(self.__commit_text()) or None
        details['revision'] = self.get_revision()
        details['author'] = str(self.__author()) or None
        if details['prn'] == '00000' and details['author'] == 'buildmgr':
            details['branch'] = None
        else:
            details['branch'] = self.__modified_branch() or None
        if DEBUG == "True":
            write_debug("[debug] svn details:", str(details))
        return details

    def __prn(self):
        '''Returns the PRN number from a Subversion transaction, or None'''
        try:
            return self.__commit_re().match(self.log()).group('prn_number')
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
            return self.__commit_re().match(self.log()).group('separator')
        except IndexError:
            sys.exit('[sep] Malformed commit message (separator missing?)')
        except AttributeError:
            sys.exit("[sep] Where's the commit message?")
        return None

    def __commit_text(self):
        '''Returns the commit text from a Subversion transaction, or None'''
        try:
            return self.__commit_re().match(self.log()).group('commit_text')
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
                (?P<commit_text>.*$)        # match commit message text
                ''', re.VERBOSE|re.MULTILINE)

    def __author(self):
        '''Returns the author of this transaction'''
        tmp = fs.svn_fs_txn_prop(self.txn, "svn:author")
        if DEBUG == "True":
            write_debug("[author]: ", tmp)
        return tmp

    # FIXME It's not a modified branch unless the transaction succeeds, so the
    # name is misleading.
    def __modified_branch(self):
        '''Returns the branch for this transaction (string)'''
        # paths looks like ['A   path/to/file1.txt\r', 'M   path/to/file2.txt']
        paths = self.changed().split('\n')
        #write_debug("[debug] paths: %s" % paths)
        branch = None

        last_line = ""
        try:
            last_line = paths[-1]
        # This could happen ... when?  Should be never.
        except IndexError:
            sys.exit("[modbranch] something broke when fetching the last line")

        # 'A   path/to/file1.txt\r' --> 'A   path', 'to', 'file1.txt\r'
        parts = os.path.normpath(last_line).split("   ")
        #write_debug("[debug] parts: %s" % parts)

        # TODO these should be in bugbranch.ini
        branches = {
                '9_10_m':       r'branches\9.10\maintenance\base',
                '10_0_m':       r'branches\10.0\maintenance\base',
                '10_0_0115':    r'branches\10.0\maintenance\10.0.0115',
                '10_0_0208':    r'branches\10.0\maintenance\10.0.0208',
                '10_0_0214':    r'branches\10.0\maintenance\10.0.0214',
                'Viper':        r'branches\projects\Viper',
                'AvayaPDS':     r'branches\projects\AvayaPDS',
                'JTAPI':        r'branches\projects\JTAPI',
                }

        #write_debug("branches: %s\n" % os.path.normpath(str(branches)))
        #write_debug("[debug] os.path.normpath(parts[1]): %s" % os.path.normpath(parts[1]))
        for abbr, branch in branches.items():
            if branch in os.path.normpath(parts[1]):
                return (abbr, branch)
        return None

    # Actually, it returns a string that looks like a list
    def changed(self):
        '''Returns the list of files changed in this transaction'''
        # txn_root = svn.fs.svn_fs_txn_root(txn)
        # txn_root = svn.fs.svn_fs_txn_root(self.txn)
#        changed_paths = fs.paths_changed(self.txn_root)
#        for key, value in changed_paths.items():
#            write_debug(str(type(key)), str(type(value)))
#        write_debug("xxx:", changed_paths.items())

        p = subprocess.Popen([SVNLOOK, 'changed', self.rpath, '-t', self.tname],
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE)
        stdout_text, stderr_text = p.communicate(None)
        if DEBUG == "True":
            write_debug("[changed] stdout:", stdout_text.strip('\n'))
            write_debug("[changed] stderr:", stderr_text.strip('\n'))
        return stdout_text.strip()

    def get_revision(self):
        '''Returns the revision of this transaction'''
        # This is a precommit hook, so the current revision is not available
        # yet.  I'm cheating a little by adding 1 to the youngest revision,
        # and hoping for the best. :)
        p = subprocess.Popen([SVNLOOK, 'youngest', self.rpath],
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE)
        stdout_text, stderr_text = p.communicate(None)
#        return stdout_text.strip()
        # ugly
        tmp = int(stdout_text.strip()) + 1
        return str(tmp)

    def modified_files(self):
        '''A better (but new and unfamiliar) way to get the changed files'''
        return fs.paths_changed(self.txn_root).keys()

    def log(self):
        '''Returns the entire SVN log message (private method)'''
        tmp = fs.svn_fs_txn_prop(self.txn, "svn:log")
        if DEBUG == "True":
            write_debug("[log]:", tmp)
        return tmp


class NetResults(object):
    '''DOCSTRING'''
    def __init__(self):
        self.conn = pyodbc.connect('''
            DRIVER={SQL Server};
            SERVER=CHINOOK;
            DATABASE=ProblemTracker;
            Trusted_Connection=yes''')
        self.cursor = self.conn.cursor()

    def get_details(self, prn_from_svn):
        '''DOCSTRING'''
        tmp = self.__prn(prn_from_svn)

        details = {}
        details['prn'] = str(tmp.PRN) or None
        details['title'] = str(tmp.Text1) or None
        details['assigned_to'] = str(tmp.Assignee) or None
        details['status'] = str(tmp.Status) or None
        details['project'] = self.__project(str(tmp.Pulldown8)) or None
        details['request_type'] = str(tmp.Pulldown2) or None
        if DEBUG == "True":
            write_debug("[bugbranch] NetResults details:", str(details))
        return details

    def __project(self, project_str):
        '''Returns a unique string for each active project'''
        projects = {
                '10.2.0000 (Charlie)': '10_2_0000',
                '10.1.0000 (Viper)': '10_1_0000',
                '10.0.0200 (10.0.SP2)': '10_0_0200',
                'Patch': 'patch',
                'No Planned Project': 'no_project',
                }
        for key, value in projects.items():
            if project_str in key:
                return (key, value)

    def __prn(self, prn):
        '''Returns the PRN contents as a list if found, or None'''
        record = self.cursor.execute('''
            SELECT PRN, Text1, Assignee, Status, Pulldown8, Pulldown2
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

    def update_record(self, prn, svn_author, svn_log, svn_rev, svn_branch,
            mod_files):
        '''Writes the validated commit message to the specified PRN'''
        # need the fields
        now = strftime("%a, %d %b %Y %H:%M:%S")
#        message = "this is a test baba booey"
        description = '\n==== Updated on %s ====' % now
        description += '\nAuthor: %s' % svn_author
        description += '\nMessage: %s' % svn_log
        description += '\nRevision: %s' % svn_rev
        description += '\nBranch: %s' % svn_branch
        # mod_files is a list
        description += '\nModified-Files:'
        for file in mod_files:
            description += '\n  %s' % file
        description += '\n'

        self.cursor.execute("""
            UPDATE NRTracker.Records
            SET BigText1 = Convert(varchar(7000), BigText1) +
            Convert(varchar(7000), ?) WHERE PRN = ?
            """, description, prn)
        self.conn.commit()


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

