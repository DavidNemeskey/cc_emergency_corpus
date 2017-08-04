package hu.mta.sztaki.hlt.parse_cc.commons;

import jnr.posix.Linux;
import jnr.posix.POSIX;
import jnr.posix.POSIXFactory;
import static jnr.posix.LinuxIoPrio.*;

/** Auxiliary functions for java.lang.System. */
public class System {
    /** Nices the process + io. Only works for Linux. */
    public static boolean fullNice() {
        POSIX posix = POSIXFactory.getNativePOSIX();
        boolean ret = posix.setpriority(1, 0, 20) == 0;
        if (posix instanceof Linux) {
            Linux lp = (Linux)posix;
            ret &= lp.ioprio_set(IOPRIO_WHO_PROCESS, 0,
                                 IOPRIO_PRIO_VALUE(IOPRIO_CLASS_BE, 7)) == 0;
        }
        return ret;
    }
}
