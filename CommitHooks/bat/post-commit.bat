@echo OFF
REM POST-COMMIT HOOK
REM
REM The post-commit hook is invoked after a commit.  Subversion runs
REM this hook by invoking a program (script, executable, binary, etc.)
REM named 'post-commit' (for which this file is a template) with the
REM following ordered arguments:
REM
REM   [1] REPOS-PATH   (the path to this repository)
REM   [2] REV          (the number of the revision just committed)
REM
REM The default working directory for the invocation is undefined, so
REM the program should set one explicitly if it cares.
REM
REM Because the commit has already completed and cannot be undone,
REM the exit code of the hook program is ignored.  The hook program
REM can use the 'svnlook' utility to help it examine the
REM newly-committed tree.
REM
REM On a Unix system, the normal procedure is to have 'post-commit'
REM invoke other programs to do the real work, though it may do the
REM work itself too.
REM
REM Note that 'post-commit' must be executable by the user(s) who will
REM invoke it (typically the user httpd runs as), and that user must
REM have filesystem-level permission to access the repository.
REM
REM On a Windows system, you should name the hook program
REM 'post-commit.bat' or 'post-commit.exe',
REM but the basic idea is the same.
REM
REM The hook program typically does not inherit the environment of
REM its parent process.  For example, a common problem is for the
REM PATH environment variable to not be set to its usual value, so
REM that subprograms fail to launch unless invoked via absolute path.
REM If you're having unexpected problems with a hook program, the
REM culprit may be unusual (or missing) environment variables.
REM
REM Here is an example hook script, for a Unix /bin/sh interpreter.
REM For more examples and pre-written hooks, see those in
REM the Subversion repository at
REM http://svn.collab.net/repos/svn/trunk/tools/hook-scripts/ and
REM http://svn.collab.net/repos/svn/trunk/contrib/hook-scripts/

REM Note, use TXN before the commit, and REV after

@ECHO ON

SETLOCAL
SET REPOS=%1
SET REV=%2
SET PYTHON=C:\Python26\python.exe

REM ############################
REM FOR TESTING ONLY
REM SET REPOS=E:\SVN\MayaRepo
REM SET REV=267
REM ############################

%PYTHON% F:\Repositories\ETCM.next\CommitHooks\EmailCommit\EmailCommit.py %REPOS% %REV%
