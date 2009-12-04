using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using log4net;
using System.Data;
using System.Data.SqlClient;
using System.Data.Odbc;
using Envision.ConfigurationManagement.Properties;

namespace Envision.ConfigurationManagement
{
    /// <summary>
    /// Class responsible for taking the Problem Tracker export and importing into database
    /// </summary>
    public class ETCMImporter
    {
        private static readonly ILog logger = LogManager.GetLogger(typeof(ETCMImporter));

        public void Run(bool fullImport)
        {
            logger.Info("Starting import into ETCM database...");

            // Read the CSV file
            DataTable export = ReadCSV();

            // Import the records into the ETCM database
            if (fullImport)
            {
                ImportFullExport(export);
            }
            else
            {
                ImportHistory(export);
            }

            logger.Info("Done importing into ETCM database.");
        }

        /// <summary>
        /// Read the given CSV file into a DataTable
        /// </summary>
        /// <param name="filename"></param>
        /// <returns></returns>
        private DataTable ReadCSV()
        {
            DataTable ptTable = null;
            OdbcConnection ptConnection = null;
            OdbcCommand ptSelect = null;
            OdbcDataAdapter ptAdapter = null;
            try
            {
                ptTable = new DataTable();

                // Setup the data reader/writer objects
                ptConnection = new OdbcConnection("Driver={Microsoft Text Driver (*.txt; *.csv)};Dbq=" + Settings.Default.ExportDirectory + ";Extensions=csv,txt");
                ptSelect = new OdbcCommand("SELECT * FROM " + PTExporter.EXPORT_FILENAME, ptConnection);
                ptAdapter = new OdbcDataAdapter(ptSelect);

                // Read CSV file into DataTable
                logger.Debug("Reading CSV file into DataTable...");
                ptConnection.Open();
                ptAdapter.Fill(ptTable);
                ptConnection.Close();
                logger.Debug("Read " + ptTable.Rows.Count + " records from CSV file.");
            }
            catch (Exception e)
            {
                logger.Error("Error reading CSV file", e);
                throw e;
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
            }
            return ptTable;
        }

        /// <summary>
        /// Import the given history changes into SQL.
        /// </summary>
        /// <param name="history"></param>
        private void ImportHistory(DataTable history)
        {
            try
            {
                // Get a comma-delimited list of RPNs for log statement
                List<string> prns = new List<string>();
                foreach (DataRow row in history.Rows)
                {
                    prns.Add(row["PRN"].ToString());
                }

                logger.Debug("Importing the following " + history.Rows.Count + " changed issues: " + string.Join(",", prns.ToArray()));

                // Update and add issues
                using (ETCMDataContext etcm = new ETCMDataContext())
                {
                    Dictionary<int, Issue> newIssues = new Dictionary<int, Issue>();

                    // Loop through the changes
                    foreach (DataRow change in history.Rows)
                    {
                        int changedPRN = change.Field<int>("PRN");

                        Issue existingIssue = (from i in etcm.Issues
                                            where i.PRN == changedPRN
                                            select i).SingleOrDefault();

                        Issue issue = existingIssue;
                        if (existingIssue == null)
                        {
                            // This is a new issue, handle case of update(s) to new issue
                            if (!newIssues.TryGetValue(changedPRN, out issue))
                            {
                                issue = new Issue();
                                newIssues.Add(changedPRN, issue);
                            }
                        }

                        UpdateIssue(issue, change);
                    }
                    etcm.Issues.InsertAllOnSubmit(newIssues.Values);
                    etcm.SubmitChanges();                    
                }

                logger.Debug("Done importing changed issues");
            }
            catch (Exception e)
            {
                logger.Error("Error imported changes into ETCM database", e);
                throw e;
            }
        }

        /// <summary>
        /// Import given full export into SQL
        /// </summary>
        /// <param name="export"></param>
        private void ImportFullExport(DataTable export)
        {
            try
            {
                logger.Debug("Importing full export which has " + export.Rows.Count + " records...");
                
                // Update and add issues
                using (ETCMDataContext etcm = new ETCMDataContext())
                {
                    foreach (DataRow exportedRow in export.Rows)
                    {
                        Issue issue = new Issue();
                        UpdateIssue(issue, exportedRow);
                        etcm.Issues.InsertOnSubmit(issue);
                    }

                    logger.Debug("Truncate issues");
                    etcm.ExecuteCommand("TRUNCATE TABLE Issue");

                    logger.Debug("Insert all issues");
                    etcm.SubmitChanges();
                    logger.Debug("Done inserting issues");
                }

                logger.Debug("Done importing full export.");
            }
            catch (Exception e)
            {
                logger.Error("Error imported changes into ETCM database", e);
                throw e;
            }
        }

        /// <summary>
        /// Boiler-plate code to update the Issue object based on 
        /// the given exported row.
        /// </summary>
        /// <param name="issue"></param>
        /// <param name="exportedRow"></param>
        private static void UpdateIssue(Issue issue, DataRow exportedRow)
        {
            DateTime dt;
            // This is the coolest code ever
            issue.PRN = exportedRow.Field<int>("PRN");
            issue.RequestType = exportedRow["Request Type"].ToString();
            issue.Title = exportedRow["Title"].ToString();
            issue.AssignedTo = exportedRow["Assigned To"].ToString();
            issue.ReportedBy = exportedRow["Reported By"].ToString();
            issue.Status = exportedRow["Status"].ToString();
            issue.Priority = exportedRow.Field<int>("Priority");
            issue.Severity = exportedRow["Severity"].ToString();
            issue.DateReported = DateTime.Parse(exportedRow["Date Reported"].ToString());
            if (DateTime.TryParse(exportedRow["Fix Date"].ToString(), out dt))
                issue.DateFixed = DateTime.Parse(exportedRow["Fix Date"].ToString());
            if (DateTime.TryParse(exportedRow["Close Date"].ToString(), out dt))
                issue.DateClosed = DateTime.Parse(exportedRow["Close Date"].ToString());
            issue.AssignedToProject = exportedRow["Assigned to Project"].ToString();
            issue.ReportedInVersion = exportedRow["Reported In Version"].ToString();
            issue.CodeReviewed = exportedRow["Code Reviewed"].ToString();
            issue.Product = exportedRow["Product"].ToString();
            issue.Component = exportedRow["Component"].ToString();
        }
    }
}
