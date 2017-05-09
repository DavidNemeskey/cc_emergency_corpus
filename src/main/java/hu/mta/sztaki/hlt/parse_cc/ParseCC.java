package hu.mta.sztaki.hlt.parse_cc;

import java.io.File;
import java.io.IOException;
import java.nio.file.FileSystem;
import java.nio.file.FileSystems;

import java.util.logging.Logger;
import java.util.logging.Level;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

import jnr.posix.POSIX;
import jnr.posix.POSIXFactory;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;

import static hu.mta.sztaki.hlt.parse_cc.Commons.formatStackTrace;
import static hu.mta.sztaki.hlt.parse_cc.Logging.configureLogging;
import static hu.mta.sztaki.hlt.parse_cc.Logging.getLevels;
import hu.mta.sztaki.hlt.parse_cc.extractors.Extractor;
import hu.mta.sztaki.hlt.parse_cc.extractors.BoilerpipeExtractor;
import hu.mta.sztaki.hlt.parse_cc.extractors.JusTextExtractor;

public class ParseCC {
    /** WARC file name pattern. */
    private static Pattern warcP = Pattern.compile("^(.+)[.]warc(?:[.]gz)?$");
    private static Logger logger;

    /** Parses the command line arguments with Commons CLI. */
    public static Namespace parseArguments(String[] args) {
        ArgumentParser parser = ArgumentParsers.newArgumentParser("ParseCC")
                .defaultHelp(true)
                .description("Parses Common Crawl WARC files into plaintext " +
                             "documents.");
        parser.addArgument("-o", "--output-dir")
                .required(true)
                .help("the output directory.");
        parser.addArgument("-e", "--extractor")
                .choices("boilerpipe", "justext")
                .setDefault("boilerpipe")
                .help("the text extractor to use.");
        parser.addArgument("-l", "--log-dir")
                .help("the log directory. If specified, a separate log file " +
                      "is created for each input file; otherwise, logs are " +
                      "written to stderr.");
        parser.addArgument("-L", "--log-level")
                .choices(getLevels())
                .setDefault("OFF")
                .help("the logging level.");
        parser.addArgument("input_file")
                .nargs("*")
                .help("an input WARC file. Note that it must have the .warc " +
                      "or .warc.gz extension.");
        try {
            return parser.parseArgs(args);
        } catch (ArgumentParserException ape) {
            parser.handleError(ape);
            System.exit(1);
            return null;  // LOL
        }
    }

    /** Returns the extractor named in the argument. */
    private static Extractor getExtractor(String extractor) {
        if ("boilerpipe".equalsIgnoreCase(extractor)) {
            return new BoilerpipeExtractor();
        } else {
            return new JusTextExtractor();
        }
    }

    /**
     * Returns the output file that corresponds to the specified input WARC.
     *
     * @param outputDirectory the output directory.
     * @param inputFile the name of the original file.
     * @param extension the extension of the output file that replaces the
     *                  .warc(.gz) extension of the original.
     * @throws IllegalArgumentException if the input file name does not end
     *                                  with .warc(.gz).
     */
    private static String getOutputFile(
            String outputDirectory, String inputFile, String extension)
            throws IllegalArgumentException {
        FileSystem fs = FileSystems.getDefault();
        String baseName = fs.getPath(inputFile).getFileName().toString();
        Matcher m = warcP.matcher(baseName);
        if (!m.matches()) {
            throw new IllegalArgumentException(
                    String.format("Not a valid input file name: %s; " +
                                  ".warc(.gz) extension missing.", baseName));
        }
        return fs.getPath(
                outputDirectory, m.group(1) + "." + extension).toString();
    }

    /** Creates a directory or exits.  */
    private static void createDirectory(String directory) {
        File f = new File(directory);
        if (!f.isDirectory()) {
            if (f.exists()) {
                errorAndExit("A file named " + directory + " already exists.");
            } else if (!f.mkdirs()) {
                errorAndExit("Could not create directory " + directory + ".");
            }
        }
    }

    /** Logs the error message and exists the program. */
    private static void errorAndExit(String message) {
        logger.severe(message);
        System.exit(1);
    }

    public static void main(String[] args) {
        Namespace ns = parseArguments(args);
        String outDir = ns.getString("output_dir");
        String logDir = ns.getString("log_dir");
        createDirectory(outDir);
        if (logDir != null) createDirectory(logDir);
        Extractor extractor = getExtractor(ns.getString("extractor"));
        logger = configureLogging(Level.parse(ns.getString("log_level")));

        POSIX posix = POSIXFactory.getNativePOSIX();
        posix.setpriority(0, 0, 20);

        for (String inputFile : ns.<String>getList("input_file")) {
            try {
                String outputFile = getOutputFile(
                        ns.getString("output_dir"), inputFile, "xml");
                if (logDir != null) {
                    logger = configureLogging(Level.parse(ns.getString("log_level")),
                                              getOutputFile(logDir, inputFile, "log"));
                }
                WARCIterator wi = new WARCIterator(inputFile, extractor);
                XMLConverter converter = new XMLConverter(outputFile);
                logger.info(String.format("Converting %s to %s...",
                                          inputFile, outputFile));
                for (WARCDocument doc : wi) {
                    converter.convert(doc);
                }
                converter.close();
            } catch (IOException ioe) {
                errorAndExit(String.format("IO Exception: %s%n%s", ioe,
                                           formatStackTrace(ioe)));
            } catch (Exception e) {
                errorAndExit(String.format("Exception: %s%n%s", e,
                                           formatStackTrace(e)));
            }
        }
    }
}
