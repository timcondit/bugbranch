# Get the Transaction ID and Repository from the command line
$txn          = $ARGV[0];
$repos        = $ARGV[1];

# Execute the SVNLOOK LOG command to get the commit message
$svnlook      = "\"C:/Subversion/bin/svnlook.exe\"";
$svnlook_cmd  = "$svnlook log -t $txn $repos";
$commit_msg   = `$svnlook_cmd`;

# Look for a properly formatted commit string "<BugNumber> - <Commit Message>"
@grep_matches = grep(/^\s*[0-9]{5}\s*[:-]\s*[^\s]+/, ($commit_msg));
$match_count  = scalar(@grep_matches);

# Return 0 for success, 1 for fail
if ($match_count == 0) {
    print STDERR "\nInvalid commit message:\n\n$commit_msg\n\nThe text must be in the following format:\n\n<BugNumber> - <Commit Message>\n";
    exit 1;
}
exit 0;
