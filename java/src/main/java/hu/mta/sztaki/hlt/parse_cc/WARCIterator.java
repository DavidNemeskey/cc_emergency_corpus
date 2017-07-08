package hu.mta.sztaki.hlt.parse_cc;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.Charset;
import static java.nio.charset.StandardCharsets.UTF_8;

import java.lang.Iterable;
import java.util.Iterator;
import java.util.logging.Logger;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.stream.Collectors;
import java.util.zip.DataFormatException;

import org.archive.io.ArchiveRecord;
import org.archive.io.ArchiveRecordHeader;
import org.archive.io.warc.WARCReader;
import org.archive.io.warc.WARCReaderFactory;

import hu.mta.sztaki.hlt.parse_cc.extractors.Extractor;

/** Reads a WARC file and iterates through it, returning  */
public class WARCIterator implements Iterable<WARCDocument>,
                                     Iterator<WARCDocument> {
    private static Pattern statusLineP = Pattern.compile(
            "^HTTP[\\S]+ ([\\d]+) [\\S]+$");
    private static Pattern httpHeaderP = Pattern.compile(
            "^([^:]+)::?[ ]?(.+)?$");
    private static Pattern charsetP = Pattern.compile(
            "charset\\s*=\\s*\"?\\s*([^\";]+?)\\s*\"?(?:;.*)?$",
            Pattern.CASE_INSENSITIVE);

    /** The extractor to use for text extraction from HTML. */
    private Extractor extractor;
    /** The next response document found. */
    private WARCDocument currentDocument;
    /** The inner iterator; the class that does the actual work. */
    private Iterator<ArchiveRecord> it;

    public WARCIterator(String warcFile, Extractor extractor)
            throws IOException {
        this.it = WARCReaderFactory.get(warcFile).iterator();
        this.extractor = extractor;
        this.currentDocument = readNextResponse();
    }

    /** Returns @c this object. */
    @Override
    public Iterator<WARCDocument> iterator() {
        return this;
    }

    @Override
    public boolean hasNext() {
        return currentDocument != null;
    }

    @Override
    public WARCDocument next() {
        WARCDocument ret = currentDocument;
        currentDocument = readNextResponse();
        return ret;
    }

    /** Looks up and returns the next valid response from the WARC file. */
    private WARCDocument readNextResponse() {
        while (it.hasNext()) {
            ArchiveRecord r = it.next();
            ArchiveRecordHeader header = r.getHeader();
            if (((String)header.getHeaderValue("WARC-Type")).equalsIgnoreCase("response")) {
                WARCDocument doc = new WARCDocument(
                        (String)header.getHeaderValue("WARC-Target-URI"),
                        (String)header.getHeaderValue("WARC-Date"));
                ByteArrayOutputStream os = new ByteArrayOutputStream();
                try {
                    r.dump(os);
                } catch (IOException ioe) {
                    assert false : "IOException while writing ByteArray?!";
                    continue;
                }
                try {
                    if (parseHTTP(doc, os)) {
                        doc.content = extractor.extract(doc.content);
                        Logger.getLogger(WARCIterator.class.getName()).finer(
                                String.format("Found document %s", doc.url));
                        return doc;
                    } else {
                        Logger.getLogger(WARCIterator.class.getName()).fine(
                                "HTTP status not OK: " + doc.url);
                    }
                } catch (DataFormatException dfe) {
                    Logger.getLogger(WARCIterator.class.getName()).fine(
                            String.format("Could not parse header for %s: %s",
                                          doc.url, dfe));
                }
            }
        }
        return null;
    }

    /**
     * Parses the HTTP response @c httpResponse into the specified @c WARCDocument.
     *
     * @return @c true, if the record was a HTTP response with status 200 (OK);
     *         @c false otherwise.
     * @throw DataFormatException if the HTTP header is invalid.
     */
    private static boolean parseHTTP(WARCDocument doc,
                                     ByteArrayOutputStream httpResponse)
            throws DataFormatException {
        try {
            BufferedReader br = new BufferedReader(new StringReader(
                        httpResponse.toString(UTF_8.name())));
            HeaderPair header = readHeader(br);
            if (header.success) {
                if (header.charset != UTF_8) {
                    br = new BufferedReader(new StringReader(
                            httpResponse.toString(header.charset.name())));
                    readHeader(br);
                }
                doc.content = br.lines().collect(Collectors.joining("\n"));
                return true;
            }
        } catch (IOException ioe) {
            assert false : "IOException while reading from String?!";
        }
        return false;
    }

    /**
     * Parses the HTTP response header loaded into @c br.
     *
     * @return a @c Pair of a boolean (whether the document is valid) and the
     *         charset of the document, if specified. It defaults to utf-8.
     */
    private static HeaderPair readHeader(BufferedReader br)
            throws IOException, DataFormatException {
        Charset encoding = UTF_8;
        String line = br.readLine();
        if (line != null) {
            Matcher m = statusLineP.matcher(line);
            if (!m.matches())
                throw new DataFormatException(
                        String.format("Invalid status line '%s'.", line));
            else if (!m.group(1).equals("200"))
                return new HeaderPair(false, encoding);
        }
        while ((line = br.readLine()) != null) {
            if (line.length() == 0) break;
            Matcher m = httpHeaderP.matcher(line); 
            if (!m.matches())
                throw new DataFormatException(
                        String.format("Invalid field line '%s'.", line));
            if (m.group(1).equals("Content-Type") && m.group(2) != null) {
                Logger.getLogger(WARCIterator.class.getName()).finer(
                        String.format("Content-Type is >%s<", m.group(2)));
                m = charsetP.matcher(m.group(2));
                if (m.find()) {
                    try {
                        Logger.getLogger(WARCIterator.class.getName()).finer(
                                String.format("Encoding >%s<", m.group(1)));
                        encoding = Charset.forName(canonicalCharset(m.group(1)));
                    } catch (IllegalArgumentException iae) {
                        throw new DataFormatException(String.format(
                                "Invalid encoding name %s", m.group(1)));
                    }
                } else {
                    Logger.getLogger(WARCIterator.class.getName()).finer(
                            String.format("No encoding"));
                }
            }
        }
        return new HeaderPair(true, encoding);
    }

    /**
     * Adds a few charset aliases -- to bad this cannot be done in Charset.
     * This is on a "best effort" basis...
     */
    private static String canonicalCharset(String cs) {
        if (cs.contains(" ")) {
            cs = cs.replace(" ", "_");
        }
        if (cs.toLowerCase().startsWith("cp-")) {
            cs = "cp" + cs.substring(3);  
        }
        return cs;
    }

    /** Type of the return value from readHeader(). */
    private static class HeaderPair {
        public Boolean success;
        public Charset charset;

        public HeaderPair(Boolean success, Charset charset) {
            this.success = success;
            this.charset = charset;
        }
    }
}
