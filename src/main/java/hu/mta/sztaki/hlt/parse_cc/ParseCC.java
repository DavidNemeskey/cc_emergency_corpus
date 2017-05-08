package hu.mta.sztaki.hlt.parse_cc;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;

import java.util.Optional;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import java.util.zip.DataFormatException;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

import de.tudarmstadt.ukp.dkpro.c4corpus.boilerplate.BoilerPlateRemoval;
import de.tudarmstadt.ukp.dkpro.c4corpus.boilerplate.impl.JusTextBoilerplateRemoval;

import net.sourceforge.argparse4j.ArgumentParsers;
import net.sourceforge.argparse4j.inf.ArgumentParser;
import net.sourceforge.argparse4j.inf.ArgumentParserException;
import net.sourceforge.argparse4j.inf.Namespace;

import org.archive.io.ArchiveRecord;
import org.archive.io.ArchiveRecordHeader;
import org.archive.io.warc.WARCReader;
import org.archive.io.warc.WARCReaderFactory;

public class ParseCC {
    /** Document content + a few fields from the WARC and HTML headers. */
    private static class MyDocument {
        /** @todo replace with DateTime. */
        public String date;
        /** The encoding used by the document. */
        public String encoding;
        /** The extracted text. */
        public String text;
    }

    private static Pattern statusLineP = Pattern.compile(
            "^HTTP[\\S]+ ([\\d]+) [\\S]+$");
    private static Pattern httpHeaderP = Pattern.compile(
            "^([^:]+): (.+)$");

    private static final BoilerPlateRemoval boilerPlateRemoval =
            new JusTextBoilerplateRemoval();

    /**
     * Parses the HTTP response @c httpResponse into the specified @c MyDocument.
     *
     * @return @c true, if the record was a HTTP response with status 200 (OK);
     *         @c false otherwise.
     * @throw DataFormatException if the HTTP header is invalid.
     */
    private static boolean parseHTTP(MyDocument doc, String httpResponse)
            throws DataFormatException {
        try {
            BufferedReader br = new BufferedReader(new StringReader(httpResponse));
            String line = br.readLine();
            if (line != null) {
                Matcher m = statusLineP.matcher(line);
                if (!m.matches())
                    throw new DataFormatException(
                            String.format("Invalid status line '%s'.", line));
                else if (!m.group(1).equals("200"))
                    return false;
            }
            while ((line = br.readLine()) != null) {
                if (line.length() == 0) break;
                Matcher m = httpHeaderP.matcher(line); 
                if (!m.matches())
                    throw new DataFormatException(
                            String.format("Invalid field line '%s'.", line));
                if (m.group(1).equals("Content-Type")) {
                    int cPos = m.group(2).lastIndexOf("charset=");
                    if (cPos != -1) {
                        doc.encoding = m.group(2).substring(cPos + 8);
                    }
                }
            }
            doc.text = br.lines().collect(Collectors.joining("\n"));
            return true;
        } catch (IOException ioe) {
            assert false : "IOException while reading from String?!";
            return false;
        }
    }

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

    public static void main(String[] args) {
        Namespace ns = parseArguments(args);
        for (String inputFile : ns.<String>getList("input_file")) {
            try {
                WARCReader wr = WARCReaderFactory.get(args[0]);
                Transformer tf = TransformerFactory.newInstance().newTransformer();
                tf.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
                tf.setOutputProperty(OutputKeys.INDENT, "yes");
                tf.setOutputProperty(OutputKeys.STANDALONE, "yes");
                StringWriter out = new StringWriter();
                StreamResult sr = new StreamResult(out);
                DocumentBuilderFactory dbf =
                        DocumentBuilderFactory.newInstance();
                DocumentBuilder builder = dbf.newDocumentBuilder();
                tf.transform(new DOMSource(builder.newDocument()), sr);
                tf.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "yes");
                for (ArchiveRecord r : wr) {
                    ArchiveRecordHeader header = r.getHeader();
                    if (((String)header.getHeaderValue("WARC-Type")).equalsIgnoreCase("response")) {
                        MyDocument doc = new MyDocument();
                        doc.date = (String)header.getHeaderValue("WARC-Date");
                        ByteArrayOutputStream os = new ByteArrayOutputStream();
                        r.dump(os);
                        try {
                            if (parseHTTP(doc, os.toString())) {
                                // TODO: add Boilerpipe as an option; jusText
                                // doesn't work for e.g. Japanese
                                doc.text = boilerPlateRemoval.getPlainText(
                                        doc.text, null);
                                Document d = builder.newDocument();
                                Element docElement = d.createElement("document");
                                d.appendChild(docElement);
                                Element dateElement = d.createElement("date");
                                docElement.appendChild(dateElement);
                                dateElement.insertBefore(d.createTextNode(doc.date),
                                                         dateElement.getLastChild());
                                Element textElement = d.createElement("text");
                                docElement.appendChild(textElement);
                                textElement.insertBefore(d.createTextNode(doc.text),
                                                         textElement.getLastChild());
                                tf.transform(new DOMSource(d), sr);
                                System.out.println(out.toString());
                                out.getBuffer().setLength(0);
                            } else {
                                System.err.println("HTTP status not OK.");
                            }
                        } catch (DataFormatException dfe) {
                            System.err.printf("Could not parse header %s%n", dfe);
                        }
                    }
                }
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
