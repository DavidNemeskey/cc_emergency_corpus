package hu.mta.sztaki.hlt.parse_cc.extractors;

import de.l3s.boilerpipe.BoilerpipeProcessingException;
import de.l3s.boilerpipe.extractors.CommonExtractors;

/** An Extractor that uses Boilerpipe. */
public class BoilerpipeExtractor implements Extractor {
    @Override
    public String extract(String html) {
        try {
            return CommonExtractors.ARTICLE_EXTRACTOR.getText(html);
        } catch (BoilerpipeProcessingException bpe) {
            return null;
        }
    }
}
