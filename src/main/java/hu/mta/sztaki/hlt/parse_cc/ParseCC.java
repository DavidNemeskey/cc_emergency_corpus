package hu.mta.sztaki.hlt.parse_cc;

import java.io.IOException;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;

import hu.mta.sztaki.hlt.parse_cc.extractors.Extractor;
import hu.mta.sztaki.hlt.parse_cc.extractors.BoilerpipeExtractor;
import hu.mta.sztaki.hlt.parse_cc.extractors.JusTextExtractor;

public class ParseCC {
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
        try{
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

    public static void main(String[] args) {
        Namespace ns = parseArguments(args);
        Extractor extractor = getExtractor(ns.getString("extractor"));
        for (String inputFile : ns.<String>getList("input_file")) {
            try {
                WARCIterator wi = new WARCIterator(inputFile, extractor);
                XMLConverter converter = new XMLConverter("ide");
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
