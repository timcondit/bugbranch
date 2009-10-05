using System;
using System.Text;
using System.Text.RegularExpressions;
using System.Timers;
using NUnit.Framework;
using Selenium;
using System.IO;
using log4net;
using System.Data.Odbc;
using log4net.Config;
using System.Collections.Generic;
using System.Data;
using System.Data.SqlClient;
using System.Configuration;

namespace Envision.ConfigurationManagement
{
    public class PTImporterClient
    {
        private static readonly ILog logger = LogManager.GetLogger(typeof(PTImporterClient));

        private const int PT_EXPORT_DELAY = 90 * 1000; // one and a half minutes
        private static readonly string EXPORT_DIR = ConfigurationManager.AppSettings["EXPORT_DIR"];
        private static readonly string EXPORT_FILE = ConfigurationManager.AppSettings["EXPORT_FILE"];
        private static readonly string EXPORT_FULL_PATH = EXPORT_DIR + EXPORT_FILE;


        private ISelenium selenium;

        public PTImporterClient()
        {
            XmlConfigurator.Configure();

            logger.Info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");
            logger.Info("Starting Problem Tracker Importer");
            logger.Info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");
        }

        public void Run()
        {
            try
            {
                StartSelenium();
                DeletePreviousExport();
                NavigateToQuery();
                ExportQuery();
                ImportQueryIntoSQL();
                StopSelenium();
            }
            catch (Exception ex)
            {
                logger.Error("Unexpected error.", ex);
            }
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
            selenium.Stop();
            logger.Debug("Selenium stopped.");
        }

        private void DeletePreviousExport()
        {
            logger.Debug("Delete previous Problem Tracker export.");
            File.Delete(EXPORT_FULL_PATH);
        }

        private void NavigateToQuery()
        {
            logger.Debug("Navigating to query...");

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
            selenium.Click("query");
            selenium.WaitForPageToLoad("30000");
            selenium.SelectFrame("relative=up");
            selenium.SelectFrame("contentFrame");
            selenium.Click("QueryList");
            selenium.Select("QueryList", "label=PTImporter");
            selenium.Click("Run");
            selenium.WaitForPageToLoad("30000");

            logger.Debug("Navigated to query.");
        }

        private void ExportQuery()
        {
            logger.Debug("Starting export from Problem Tracker...");
            selenium.Click("link=Export");
            System.Threading.Thread.Sleep(PT_EXPORT_DELAY); // wait for the export to finish
            logger.Debug("Done exporting from Problem Tracker.");
        }

        private void ImportQueryIntoSQL()
        {
            logger.Info("Starting import into SQL...");

            DataTable ptTable = new DataTable();
            OdbcConnection ptConnection = null;
            OdbcCommand ptSelect = null;
            OdbcDataAdapter ptAdapter = null;

            SqlConnection etcmConnection = null;
            SqlCommand truncateCommand = null;
            SqlBulkCopy bulkCopy = null;

            try
            {
                // Setup the data reader/writer objects
                ptConnection = new OdbcConnection("Driver={Microsoft Text Driver (*.txt; *.csv)};Dbq=" + EXPORT_DIR + ";Extensions=csv,txt");
                ptSelect = new OdbcCommand("SELECT * FROM " + EXPORT_FILE, ptConnection);
                ptAdapter = new OdbcDataAdapter(ptSelect);

                etcmConnection = new SqlConnection(
                    ConfigurationManager.ConnectionStrings["ETCMConnectionString"].ConnectionString);
                truncateCommand = new SqlCommand("TRUNCATE TABLE Issue", etcmConnection);
                bulkCopy = new SqlBulkCopy(etcmConnection);
                bulkCopy.DestinationTableName = "Issue";

                // Read CSV file into DataTable
                logger.Debug("Read CSV file into DataTable.");
                ptConnection.Open();
                ptAdapter.Fill(ptTable);
                ptConnection.Close();

                // Bulk copy DataTable into SQL
                logger.Debug("Bulk copy DataTable into SQL.");
                etcmConnection.Open();
                truncateCommand.ExecuteNonQuery();
                bulkCopy.WriteToServer(ptTable);
                etcmConnection.Close();

                logger.Info("Done importing into SQL.");
            }
            catch (Exception ex)
            {
                logger.Error("Error importing CSV file into SQL", ex);
            }
            finally
            {
                if (ptAdapter != null)
                    ptAdapter.Dispose();
                if (ptSelect != null)
                    ptSelect.Dispose();
                if (ptConnection != null)
                {
                    ptConnection.Close();
                    ptConnection.Dispose();
                }

                if (bulkCopy != null)
                    bulkCopy.Close();
                if (truncateCommand != null)
                    truncateCommand.Dispose();
                if (etcmConnection != null)
                {
                    etcmConnection.Close();
                    etcmConnection.Dispose();
                }
            }
        }

        [STAThread]
        public static void Main(string[] args)
        {
            PTImporterClient p = new PTImporterClient();
            p.Run();
        }
    }
}
