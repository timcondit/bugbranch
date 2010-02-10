using System;
using System.Text;
using System.Text.RegularExpressions;
using System.Timers;
using log4net;
using log4net.Config;
using System.Configuration;
using System.Linq;

namespace Envision.ConfigurationManagement
{
    public class PTImporterClient
    {
        private const string LAST_IMPORT_PROPERTY = "LastImport";

        private static readonly ILog logger = LogManager.GetLogger(typeof(PTImporterClient));

        private PTExporter exporter;
        private ETCMImporter importer;

        public PTImporterClient()
        {
            XmlConfigurator.Configure();
            exporter = new PTExporter();
            importer = new ETCMImporter();
        }

        public void Run()
        {
            try
            {
                logger.Info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");
                logger.Info("Starting Problem Tracker Importer");
                logger.Info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");
                logger.Info("Performing history import");

                RunHistoryImport();
            }
            catch (Exception ex)
            {
                logger.Error("Unexpected error.", ex);
            }
        }

        /// <summary>
        /// Run the history import, one chunk at a time if necessary
        /// </summary>
        private void RunHistoryImport()
        {
            using (ETCMDataContext context = new ETCMDataContext())
            {
                DateTime? lastImport = null;
                DateTime now, historyStart, historyEnd;
                do
                {
                    now = DateTime.Now;

                    // Get the last import time
                    ETCMProperty lastImportProp = (from e in context.ETCMProperties
                                                   where e.PropertyName == LAST_IMPORT_PROPERTY
                                                   select e).SingleOrDefault();
                    if (lastImportProp != null)
                        lastImport = DateTime.Parse(lastImportProp.PropertyValue); ;

                    // Determine the start time of the history query
                    historyStart = lastImport ?? PTExporter.PT_CREATED_DATE;

                    // Determine the end time of the history query
                    historyEnd = now;
                    if (now - historyStart > PTExporter.MAX_HISTORY)
                    {
                        logger.Debug("The history from " + historyStart.ToString() + " to " + now + " is too long, limiting.");
                        historyEnd = historyStart.Add(PTExporter.MAX_HISTORY);
                    }

                    logger.Info("Importing history from timeframe (" + historyStart.ToString() + " - " + historyEnd.ToString() + ").");
                    // Run the export, and if there is history to export, import it
                    if (exporter.Run(historyStart, historyEnd))
                        importer.Run();

                    // Update the last import time
                    if (lastImportProp == null)
                    {
                        lastImportProp = new ETCMProperty();
                        context.ETCMProperties.InsertOnSubmit(lastImportProp);
                    }
                    lastImportProp.PropertyValue = historyEnd.ToString();
                    context.SubmitChanges();

                } while (historyEnd < now);
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
