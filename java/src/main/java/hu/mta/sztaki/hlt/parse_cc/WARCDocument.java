package hu.mta.sztaki.hlt.parse_cc;

/** Contains the data for a document extracted from a WARC file. */
public class WARCDocument {
    /** The URL. */
    public final String url;
    /** The date of the document (crawl?). */
    public final String date;
    /** The document content. */
    public String content;

    public WARCDocument(final String url, final String date) {
        this.url = url;
        this.date = date;
    }
}
