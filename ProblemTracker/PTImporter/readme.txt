To run:
	1. Run selenium-server-1.0.1\start_server.bat
	2. Run PTImporterClient\bin\Release\PTImporterClient.exe
	
	Note: PTImporterClient.exe can be set up as a scheduled task,
		but Selenium Server must be running the whole time

PTImporterClient.exe.config:
	ETCMConnectionString - Connection string to ETCM database
	ExportDirectory - direcotry where the csv files are exported (see note below)
	FullExportFile - file name of full export
	HistoryExportFile - file name when doing history export
	FullExportDelayMS - milliseconds to sleep while waiting for the full export to finish
	HistoryExportDelayMS - milliseconds to sleep while waiting for the history export to finish
	HistoryMinutes - the number of minutes of history to export

Full Import:
	To perform a full import (imports an export of all records from Problem Tracker) pass "fullImport" as command-line argument:
		ex. PTImporterClient.exe fullImport

Note about ExportDirectory:
	If you want to change the export path, you must change it in PTImporterClient/settings.settings
		and also in the Firefox profile.
		See http://girliemangalo.wordpress.com/2009/02/05/creating-firefox-profile-for-your-selenium-rc-tests/

