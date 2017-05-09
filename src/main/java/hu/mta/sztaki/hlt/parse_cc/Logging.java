package hu.mta.sztaki.hlt.parse_cc;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;

import java.io.IOException;

import java.util.Collection;
import java.util.Collections;
import java.util.SortedMap;
import java.util.TreeMap;
import java.util.logging.FileHandler;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.LogManager;
import java.util.logging.SimpleFormatter;
import java.util.logging.StreamHandler;

/** Logging-related functionality. */

public class Logging {
    /** Enumerates the logging levels available. */
    public static Collection<String> getLevels() {
        SortedMap<Integer, String> map = new TreeMap<Integer, String>(
                Collections.reverseOrder());
        for (Field f : Level.class.getDeclaredFields()) {
            int mod = f.getModifiers();
            if (Modifier.isStatic(mod) && Modifier.isPublic(mod)) {
                try {
                    map.put(((Level)f.get(null)).intValue(), f.getName());
                } catch (IllegalAccessException iae) {
                    System.err.println(iae);
                }
            }
        }
        return map.values();
    }

    /**
     * Configures some basic logging to logFile and gets rid of all Handlers
     * in the system to suppress library logging.
     */
    public static Logger configureLogging(Level level, String logFile)
            throws IOException {
        LogManager.getLogManager().reset();
        // Package-level logger so that the other classes can use it.
        Logger logger = Logger.getLogger(Logging.class.getPackage().getName());
        logger.setLevel(level);
        Handler h;
        if (logFile != null) {
            h = new FileHandler(logFile);
            h.setFormatter(new SimpleFormatter());
        } else {
            h = new StreamHandler(System.err, new SimpleFormatter());
        }
        h.setLevel(level);
        logger.addHandler(h);
        return logger;
    }

    /**
     * Configures some basic logging to stderr and gets rid of all Handlers
     * in the system to suppress library logging.
     */
    public static Logger configureLogging(Level level) {
        try {
            return configureLogging(level, null);
        } catch (IOException ioe) {
            assert false : "This branch does not throw IOException.";
            return null;
        }
    }
}
