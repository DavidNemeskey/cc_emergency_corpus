package hu.mta.sztaki.hlt.parse_cc.commons;

import java.io.PrintWriter;
import java.io.StringWriter;

/** Auxiliary functions for java.lang. */
public class Lang {
    public static String formatStackTrace(Throwable t) {
        StringWriter sw = new StringWriter();
        PrintWriter pw = new PrintWriter(sw);
        t.printStackTrace(pw);
        return sw.toString();
    }
}
