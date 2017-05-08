package hu.mta.sztaki.hlt.parse_cc.extractors;

import java.io.IOException;

import de.tudarmstadt.ukp.dkpro.c4corpus.boilerplate.BoilerPlateRemoval;
import de.tudarmstadt.ukp.dkpro.c4corpus.boilerplate.impl.JusTextBoilerplateRemoval;

/** An Extractor that uses Boilerpipe. */
public class JusTextExtractor implements Extractor {
    private final BoilerPlateRemoval boilerPlateRemoval =
            new JusTextBoilerplateRemoval();

    @Override
    public String extract(String html) {
        try {
            return boilerPlateRemoval.getPlainText(html, null);
        } catch (IOException ioe) {
            return null;
        }
    }
}
