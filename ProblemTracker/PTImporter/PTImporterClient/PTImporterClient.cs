using System;
using System.Text;
using System.Text.RegularExpressions;
using System.Timers;
using log4net;
using log4net.Config;
using System.Configuration;

namespace Envision.ConfigurationManagement
{
    public class PTImporterClient
    {
        private static readonly ILog logger = LogManager.GetLogger(typeof(PTImporterClient));

        private PTExporter exporter;
        private ETCMImporter importer;

        public PTImporterClient()
        {
            XmlConfigurator.Configure();
            exporter = new PTExporter();
            importer = new ETCMImporter();
        }

        public void Run(bool fullImport)
        {
            try
            {
                logger.Info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");
                logger.Info("Starting Problem Tracker Importer");
                logger.Info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");
                logger.Info("Performing " + (fullImport ? "full" : "history") + " import");

                // Make sure an export was performed before importing
                if (exporter.Run(fullImport))
                    importer.Run(fullImport);
            }
            catch (Exception ex)
            {
                logger.Error("Unexpected error.", ex);
            }
        }

        [STAThread]
        public static void Main(string[] args)
        {
            PTImporterClient p = new PTImporterClient();

            bool fullImport = args.Length > 0 && args[0].ToLower() == "fullimport";
            p.Run(fullImport);
        }
    }
}
