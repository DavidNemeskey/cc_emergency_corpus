package hu.mta.sztaki.hlt.parse_cc.extractors;

/** Extracts text from HTML. */
public interface Extractor {
    /**
     * Extracts text from HTML.
     * @param html the raw HTML.
     * @return the extracted text.
     */
    public String extract(String html);
}
