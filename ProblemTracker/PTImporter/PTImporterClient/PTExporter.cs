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
        private static readonly ILog logger = LogManager.GetLogger(typeof(PTExporter));
        private const int PT_EXPORT_DELAY = 15 * 1000; // 15 seconds
        private ISelenium selenium;

        public bool Run(bool fullImport)
        {
            bool success = false;
            bool didExport = false;
            try
            {
                logger.Info("Start exporting issues from Problem Tracker...");
                StartSelenium();
                DeletePreviousFullExport();
                DeletePreviousHistoryExport();
                Login();
                if (fullImport)
                {
                    NavigateToFullQuery();
                    ExportFullQuery();
                    didExport = true;
                }
                else
                {
                    NavigateToHistoryQuery();
                    didExport = ExportHistoryQuery();
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

        private void DeletePreviousFullExport()
        {
            logger.Debug("Delete previous Problem Tracker export.");
            File.Delete(Settings.Default.ExportDirectory + Settings.Default.FullExportFile);
        }

        private void DeletePreviousHistoryExport()
        {
            logger.Debug("Delete previous Problem Tracker export.");
            File.Delete(Settings.Default.ExportDirectory + Settings.Default.HistoryExportFile);
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

        private void NavigateToHistoryQuery()
        {
            logger.Debug("Navigating to history query for last " + Settings.Default.HistoryMinutes + " minutes...");

            selenium.Click("history");
            selenium.WaitForPageToLoad("30000");
            selenium.SelectFrame("relative=up");
            selenium.SelectFrame("contentFrame");
            selenium.Click("//input[@value='  Clear  ']");
            selenium.Type("HistoryDate_after", DateTime.Now.AddMinutes(-Settings.Default.HistoryMinutes).ToString()); // get history of last hour
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

            logger.Debug("Done exporting from Problem Tracker.");
        }

        /// <summary>
        /// Export the history query from Problem Tracker
        /// </summary>
        /// <returns></returns>
        private bool ExportHistoryQuery()
        {
            bool didExport = false;
            logger.Debug("Starting export from Problem Tracker...");

            // If there were no changes, there will be no Export link
            if (selenium.IsElementPresent("link=Export"))
            {
                selenium.Click("link=Export");
                System.Threading.Thread.Sleep(Settings.Default.HistoryExportDelayMS); // wait for the export to finish
                didExport = true;
            }
            else
            {
                logger.Info("There were no changes in the last " + Settings.Default.HistoryMinutes + " minutes.");
            }

            logger.Debug("Done exporting from Problem Tracker.");
            return didExport;
        }
    }
}
