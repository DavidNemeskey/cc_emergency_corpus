package hu.mta.sztaki.hlt.parse_cc;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.FileSystem;
import java.nio.file.FileSystems;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;

import hu.mta.sztaki.hlt.parse_cc.extractors.Extractor;
import hu.mta.sztaki.hlt.parse_cc.extractors.BoilerpipeExtractor;
import hu.mta.sztaki.hlt.parse_cc.extractors.JusTextExtractor;

public class ParseCC {
    /** WARC file name pattern. */
    private static Pattern warcP = Pattern.compile("^(.+)[.]warc(?:[.]gz)?$");

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
                .setDefault("boilerpipe")
                .choices("boilerpipe", "justext")
                .help("the text extractor to use.");
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
     * @throws IllegalArgumentException if the input file name does not end
     *                                  with .warc(.gz).
     */
    private static String getOutputFile(
            String outputDirectory, String inputFile)
            throws IllegalArgumentException {
        FileSystem fs = FileSystems.getDefault();
        String baseName = fs.getPath(inputFile).getFileName().toString();
        Matcher m = warcP.matcher(baseName);
        if (!m.matches()) {
            throw new IllegalArgumentException(
                    String.format("Not a valid input file name: %s; " +
                                  ".warc(.gz) extension missing.", baseName));
        }
        return fs.getPath(outputDirectory, m.group(1) + ".xml").toString();
    }

    public static void main(String[] args) {
        Namespace ns = parseArguments(args);
        Extractor extractor = getExtractor(ns.getString("extractor"));
        for (String inputFile : ns.<String>getList("input_file")) {
            try {
                String outputFile = getOutputFile(
                        ns.getString("output_dir"), inputFile);
                WARCIterator wi = new WARCIterator(inputFile, extractor);
                XMLConverter converter = new XMLConverter(outputFile);
                for (WARCDocument doc : wi) {
                    converter.convert(doc);
                }
                converter.close();
            } catch (IOException ioe) {
                System.err.printf("IO Exception: %s%n", ioe);
                ioe.printStackTrace(System.err);
                System.exit(1);
            } catch (Exception e) {
                System.err.printf("Exception: %s%n", e);
                e.printStackTrace(System.err);
                System.exit(1);
            }
        }
    }
}
