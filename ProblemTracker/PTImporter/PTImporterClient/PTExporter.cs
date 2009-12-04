using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.IO;
using log4net;
using Selenium;
using Envision.ConfigurationManagement.Properties;


namespace Envision.ConfigurationManagement
{
    /// <summary>
    /// Class responsible for exporting records from Problem Tracker
    /// </summary>
    public class PTExporter
    {
        public const string EXPORT_FILENAME = "PTRecords.csv";
        public const string SCHEMA_FILENAME = "schema.ini";
        public static readonly TimeSpan MAX_HISTORY = new TimeSpan(30, 0, 0, 0);
        public static readonly DateTime PT_CREATED_DATE = new DateTime(2006, 2, 1);

        private static readonly ILog logger = LogManager.GetLogger(typeof(PTExporter));
        private ISelenium selenium;

        public bool Run(bool fullImport, DateTime? historyStart, DateTime? historyEnd)
        {
            bool success = false;
            bool didExport = false;
            try
            {
                logger.Info("Start exporting issues from Problem Tracker...");
                StartSelenium();
                DeletePreviousExport();
                CopyExportSchema();
                Login();
                if (fullImport)
                {
                    NavigateToFullQuery();
                    ExportFullQuery();
                    didExport = true;
                }
                else
                {
                    NavigateToHistoryQuery((DateTime)historyStart, (DateTime)historyEnd);
                    didExport = ExportHistoryQuery((DateTime)historyStart, (DateTime)historyEnd);
                }
                success = true;
            }
            catch (Exception e)
            {
                logger.Error("Error exporting issues from Problem Tracker", e);
                throw e;
            }
            finally
            {
                StopSelenium();
            }

            if (success)
                logger.Info("Done exporting issues from Problem Tracker.");

            return didExport;
        }

        private void StartSelenium()
        {
            logger.Debug("Constructing DefaultSelenium...");
            selenium = new DefaultSelenium("localhost", 4444, "*chrome", "http://ws8.nrtracker.com/");
            logger.Debug("DefaultSelenium constructed.");

            logger.Debug("Starting Selenium...");
            selenium.Start();
            logger.Debug("Selenium started.");
        }

        private void StopSelenium()
        {
            logger.Debug("Stopping Selenium...");
            if (selenium != null)
            {
                selenium.Stop();
            }
            logger.Debug("Selenium stopped.");
        }

        private void DeletePreviousExport()
        {
            logger.Debug("Delete previous Problem Tracker export.");
            File.Delete(Settings.Default.ExportDirectory + EXPORT_FILENAME);
            File.Delete(Settings.Default.ExportDirectory + Settings.Default.FullExportFile);
            File.Delete(Settings.Default.ExportDirectory + Settings.Default.HistoryExportFile);
        }

        /// <summary>
        /// ODBC works best when there's a schema.ini file along-side the csv file
        /// </summary>
        private void CopyExportSchema()
        {
            File.Delete(Settings.Default.ExportDirectory + SCHEMA_FILENAME);
            File.Copy(SCHEMA_FILENAME, Settings.Default.ExportDirectory + SCHEMA_FILENAME, true);
        }

        private void Login()
        {
            logger.Debug("Logging in to Problem Tracker...");

            selenium.Open("http://ws8.nrtracker.com/envision/ptlogin.asp");
            selenium.Type("UserId", "etsupport");
            selenium.Type("Password", "password");
            selenium.Click("Login");
            selenium.WaitForPageToLoad("30000");
            if (selenium.IsElementPresent("name=yes"))
            {
                selenium.Click("yes"); // previous login still active, do you wish to end current active session?
                selenium.WaitForPageToLoad("30000");
            }
            selenium.SelectFrame("tempmain");
            selenium.SelectFrame("buttonFrame");

            logger.Debug("Logged in to Problem Tracker.");
        }

        private void NavigateToFullQuery()
        {
            logger.Debug("Navigating to full query...");

            selenium.Click("query");
            selenium.WaitForPageToLoad("30000");
            selenium.SelectFrame("relative=up");
            selenium.SelectFrame("contentFrame");
            selenium.Click("QueryList");
            selenium.Select("QueryList", "label=PTImporter");
            selenium.Click("Run");
            selenium.WaitForPageToLoad("30000");

            logger.Debug("Navigated to full query.");
        }

        private void NavigateToHistoryQuery(DateTime historyStart, DateTime historyEnd)
        {
            logger.Debug("Navigating to history query for timeframe (" + historyStart.ToString() + " - " + historyEnd.ToString() + ")...");

            selenium.Click("history");
            selenium.WaitForPageToLoad("30000");
            selenium.SelectFrame("relative=up");
            selenium.SelectFrame("contentFrame");
            selenium.Click("//input[@value='  Clear  ']");
            selenium.Type("HistoryDate_after", historyStart.ToString());
            selenium.Type("HistoryDate_before", historyEnd.ToString());
            selenium.RemoveSelection("HistoryColumns", "value=ActionDate");
            selenium.RemoveSelection("HistoryColumns", "value=Action");
            selenium.RemoveSelection("HistoryColumns", "value=ActionBy");
            selenium.RemoveSelection("HistoryColumns", "value=Interface");
            selenium.RemoveSelection("HistoryColumns", "value=Comment");
            selenium.RemoveSelection("HistoryColumns", "value=PreviousStatus");
            selenium.RemoveSelection("HistoryColumns", "value=Status");
            selenium.RemoveSelection("HistoryColumns", "value=PreviousAssignee");
            selenium.RemoveSelection("HistoryColumns", "value=Assignee");
            selenium.RemoveSelection("HistoryColumns", "value=PreviousProduct");
            selenium.RemoveSelection("HistoryColumns", "value=Product");
            selenium.Select("ReportLayoutID", "label=PTImporter");
            selenium.Click("//input[@value=' Run Query ']");
            selenium.WaitForPageToLoad("30000");

            logger.Debug("Navigated to history query.");
        }

        /// <summary>
        /// Export the full query from Problem Tracker
        /// </summary>
        private void ExportFullQuery()
        {
            logger.Debug("Starting export from Problem Tracker...");

            selenium.Click("link=Export");
            System.Threading.Thread.Sleep(Settings.Default.FullExportDelayMS); // wait for the export to finish

            // Rename the exported csv file
            File.Move(Settings.Default.ExportDirectory + Settings.Default.FullExportFile,
                Settings.Default.ExportDirectory + EXPORT_FILENAME);

            logger.Debug("Done exporting from Problem Tracker.");
        }

        /// <summary>
        /// Export the history query from Problem Tracker
        /// </summary>
        /// <returns></returns>
        private bool ExportHistoryQuery(DateTime historyStart, DateTime historyEnd)
        {
            bool didExport = false;
            logger.Debug("Starting export from Problem Tracker...");

            // If there were no changes, there will be no Export link
            if (selenium.IsElementPresent("link=Export"))
            {
                selenium.Click("link=Export");
                System.Threading.Thread.Sleep(Settings.Default.HistoryExportDelayMS); // wait for the export to finish
                didExport = true;

                // Rename the exported csv file
                File.Move(Settings.Default.ExportDirectory + Settings.Default.HistoryExportFile,
                    Settings.Default.ExportDirectory + EXPORT_FILENAME);
            }
            else
            {
                logger.Info("There were no changes in timeframe (" + historyStart.ToString() + " - " + historyEnd.ToString() + ").");
            }

            logger.Debug("Done exporting from Problem Tracker.");
            return didExport;
        }
    }
}
