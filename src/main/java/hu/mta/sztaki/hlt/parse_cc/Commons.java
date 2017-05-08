package hu.mta.sztaki.hlt.parse_cc;

import java.io.PrintWriter;
import java.io.StringWriter;

/** Functions that should exist in the standard library, but do not. */
public class Commons {
    public static String formatStackTrace(Throwable t) {
        StringWriter sw = new StringWriter();
        PrintWriter pw = new PrintWriter(sw);
        t.printStackTrace(pw);
        return sw.toString();
    }
}
