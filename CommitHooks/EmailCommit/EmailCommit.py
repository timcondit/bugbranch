
perl = r'"C:\strawberry\perl\bin\perl.exe"'
svnnotify_path = r'"C:\strawberry\perl\bin\svnnotify"'
svnlook_path = r'"C:\Subversion\bin\svnlook.exe"'
smpt_server = 'corpserv04.acme.envisiontelephony.com'
checkin_email = 'checkin@envisioninc.com'
files_not_uninstalled_email = 'engineering@envisioninc.com'

files_not_uninstalled = [
		'/src/clients/centricity/ET/web.config',
		'/src/clients/centricity/ET/Configuration/centricity.config',
		'/src/clients/centricity/ET/Configuration/connections.config',
		'/src/clients/centricity/Analytics/DeployAnalyticsTool/app.config',
		'/config/server/EnvisionServer.properties',
		'/config/server/log4j.properties',
		'/config/chanmgr/chanmgr_common.xsd',
		'/config/chanmgr/ChanMgrSvc.config',
		'/config/chanmgr/ChannelManager.DMCC.xml',
		'/config/chanmgr/ChannelManager.ipx.SIP.xml',
		'/config/chanmgr/ChannelManager.ipx.sr.xml',
		'/config/chanmgr/ChannelManager.ipx.xml',
		'/config/chanmgr/ChannelManager.xml',
		'/config/chanmgr/DMCCWrapperLogging.xml',
		'/config/chanmgr/eventdata.analog.xml',
		'/config/chanmgr/EventData.aspect.xml',
		'/config/chanmgr/eventdata.avaya.xml',
		'/config/chanmgr/eventdata.ipx.xml',
		'/config/chanmgr/eventdata.ipxSR.xml',
		'/config/chanmgr/eventdata.mitel.xml',
		'/config/chanmgr/eventdata.nortel.xml',
		'/config/chanmgr/eventdata.siemens.xml',
		'/config/chanmgr/eventdata.xsd',
		'/config/chanmgr/states.analog.xml',
		'/config/chanmgr/states.aspect.xml',
		'/config/chanmgr/states.avaya.xml',
		'/config/chanmgr/states.cisco.sip.xml',
		'/config/chanmgr/states.dialogic.xml',
		'/config/chanmgr/states.DMCC.xml',
		'/config/chanmgr/states.empty.xml',
		'/config/chanmgr/states.ipx.xml',
		'/config/chanmgr/states.ipxSIP.xml',
		'/config/chanmgr/states.ipxSR.xml',
		'/config/chanmgr/states.mitel.xml',
		'/config/chanmgr/states.nortel.xml',
		'/config/chanmgr/states.siemens.xml',
		'/config/chanmgr/states.trunk.isdn.xml',
		'/config/chanmgr/states.trunk.rbs.1.xml',
		'/config/chanmgr/states.xsd',
		'/config/webserver/log4j.properties',
		'/src/winservices/WMWrapperService/Service/App.config',
		]

import sys
import subprocess

def emailrevision(repo, rev):

	# Call to SVN::Notify
	# max-diff-length is (1024*512) = 524288 = 512k
	mailError =  subprocess.call(perl + ' '
		+  svnnotify_path
		+ ' --svnlook ' + svnlook_path
		+ ' --repos-path ' + repo
		+ ' --revision ' + rev
		+ ' --smtp ' + smpt_server
		+ ' --to ' + checkin_email
		+ ' --with-diff --max-diff-length 524288 '
		+ ' --subject-cx --handler HTML::ColorDiff')

	if mailError != 0:
		sys.exit(mailError)


def email_files_not_uninstalled(repo, rev):
	# Call to svnlook to get a list of modified files
	svnlook = subprocess.Popen(svnlook_path + ' changed -r ' + rev + ' ' + repo,
			stdout=subprocess.PIPE)
	svnlook.wait()
	if (svnlook.returncode != 0):
		sys.exit(svnlookError)
	
	# Get the output from svnlook
	svnlookOutput, svnlookError = svnlook.communicate()

	# Build a list of the files we're interested in
	filesOfInterest = []
	for filepath in files_not_uninstalled:
		if svnlookOutput.find(filepath) != -1:
			filesOfInterest.append(filepath)

	if len(filesOfInterest) > 0:
		# Build a string of the files 
		filesOfInterestStr = '..........' + '..........'.join(filesOfInterest)

		# Call to SVN::Notify with custom subject and header
		# max-diff-length is (1024*512) = 524288 = 512k
		mailError = subprocess.call(perl + ' '
			+  svnnotify_path
			+ ' --svnlook ' + svnlook_path
			+ ' --repos-path ' + repo
			+ ' --revision ' + rev
			+ ' --smtp ' + smpt_server
			+ ' --to ' + files_not_uninstalled_email
			+ ' --subject-prefix \"A sticky file was changed .....\"'
			+ ' --header \"Note that this revision contains files which will not be uninstalled. \
				Make sure you install or update the following files or you may have issues: '
				+ filesOfInterestStr + '\"'
			+ ' --with-diff --max-diff-length 524288 '
			+ ' --handler HTML::ColorDiff')

		if mailError != 0:
			sys.exit(mailError)


if __name__ == '__main__':
	repo = sys.argv[1]
	rev = sys.argv[2]
	emailrevision(repo, rev)
#	email_files_not_uninstalled(repo, rev)
