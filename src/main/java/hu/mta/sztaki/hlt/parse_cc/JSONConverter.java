package hu.mta.sztaki.hlt.parse_cc;

import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

/**
 * Converts a stream (not @c Stream) of @c WARCDocument objects to a JSON file.
 */
public class JSONConverter {
    /** The converter object. */
    private Gson gson;
    /** The writer to the output file. */
    private Writer writer;

    /**
     * Creates the object.
     *
     * @param outputFile the name of the output file.
     */
    public JSONConverter(String outputFile) throws IOException {
        gson = new GsonBuilder().setPrettyPrinting().create();
        writer = new BufferedWriter(new OutputStreamWriter(
                new FileOutputStream(outputFile), "utf-8"));
    }

    /**
     * Converts a document.
     *
     * @param document the document.
     */
    public void convert(WARCDocument document) throws IOException {
        String json = gson.toJson(document);
        writer.write(json);
    }

    /** Closes the output stream. */
    public void close() throws IOException {
        writer.close();
    }
}
