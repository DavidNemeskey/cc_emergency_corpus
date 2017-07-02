package hu.mta.sztaki.hlt.parse_cc;

import java.io.IOException;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.util.zip.GZIPOutputStream;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

/**
 * Converts a stream (not @c Stream) of @c WARCDocument objects to a
 * compressed JSON-per-line file.
 */
public class JSONConverter {
    /** The converter object. */
    private Gson gson;
    /** The writer to the output file. */
    private PrintWriter writer;

    /**
     * Creates the object.
     *
     * @param outputFile the name of the output file.
     */
    public JSONConverter(String outputFile) throws IOException {
        gson = new GsonBuilder().create();
        OutputStream os = new FileOutputStream(outputFile);
        os = new GZIPOutputStream(os) {{def.setLevel(5);}};
        writer = new PrintWriter(new OutputStreamWriter(os, "utf-8"));
    }

    /**
     * Converts a document.
     *
     * @param document the document.
     */
    public void convert(WARCDocument document) throws IOException {
        String json = gson.toJson(document);
        writer.println(json);
    }

    /** Closes the output stream. */
    public void close() throws IOException {
        writer.close();
    }
}
