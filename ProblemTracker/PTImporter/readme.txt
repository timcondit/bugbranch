To run:
	1. Run selenium-server-1.0.1\start_server.bat
	2. Run PTImporterClient\bin\Release\PTImporterClient.exe
	
	Note: PTImporterClient.exe can be set up as a scheduled task,
		but Selenium Server must be running the whole time

PTImporterClient.exe.config:
	ETCMConnectionString - Connection string to ETCM database
	ExportDirectory - direcotry where the csv files are exported (see note below)
	HistoryExportFile - file name when doing history export
	HistoryExportDelayMS - milliseconds to sleep while waiting for the history export to finish

Note about ExportDirectory:
	If you want to change the export path, you must change it in PTImporterClient/settings.settings
		and also in the Firefox profile located at PTImporterClient\pt_importer_ff_profile.
		See http://girliemangalo.wordpress.com/2009/02/05/creating-firefox-profile-for-your-selenium-rc-tests/

