package hu.mta.sztaki.hlt.parse_cc;

import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

/**
 * Converts a stream (not @c Stream) of @c WARCDocument objects to an XML file.
 */
public class XMLConverter {
    /** The XSLT transformer that generates the file. */
    private Transformer tf;
    /** The stream result that wraps the file @c Writer. */
    private StreamResult sr;
    /** For @c Document creation. */
    private DocumentBuilder builder;

    /**
     * Creates the object.
     *
     * @param outputFile the name of the output file.
     * @throws IOException if an IO error happens.
     * @throws TransformerException if you were betrayed by a Decepticon.
     * @throws ParserConfigurationException no idea.
     */
    public XMLConverter(String outputFile) throws IOException,
                                                  ParserConfigurationException,
                                                  TransformerException {
        // The transformer
        tf = TransformerFactory.newInstance().newTransformer();
        tf.setOutputProperty(OutputKeys.ENCODING, "UTF-8");
        tf.setOutputProperty(OutputKeys.INDENT, "yes");
        tf.setOutputProperty(OutputKeys.STANDALONE, "yes");
        sr = new StreamResult(new OutputStreamWriter(
                    new FileOutputStream(outputFile), "utf-8"));
        // Put an empty document into the file to generate the XML header ...
        builder = DocumentBuilderFactory.newInstance().newDocumentBuilder();
        tf.transform(new DOMSource(builder.newDocument()), sr);
        // ... and then suppress the header for the real documents. 
        tf.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "yes");
    }

    /**
     * Converts a document.
     *
     * @param document the document.
     * @throws TransformerException if you couldn't transform into a car.
     */
    public void convert(WARCDocument document) throws TransformerException {
        Document d = builder.newDocument();
        Element docElement = d.createElement("document");
        d.appendChild(docElement);
        addText(d, docElement, "url", document.url);
        addText(d, docElement, "date", document.date);
        addText(d, docElement, "text", document.content);
        tf.transform(new DOMSource(d), sr);
    }

    /**
     * Adds a text element.
     *
     * @param document needed for creating the element object.
     * @param parent the element to add the new text node to.
     * @param name the name of the new (text) element.
     * @param value the text value.
     */
    private void addText(Document document, Element parent,
                         String name, String value) {
        Element textElement = document.createElement(name);
        parent.appendChild(textElement);
        textElement.insertBefore(document.createTextNode(value),
                                 textElement.getLastChild());
    }

    /** Closes the output stream. */
    public void close() throws IOException {
        sr.getWriter().close();
    }
}
