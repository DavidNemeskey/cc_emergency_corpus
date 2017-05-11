package hu.mta.sztaki.hlt.parse_cc.commons;

import jnr.posix.POSIX;
import jnr.posix.POSIXFactory;

/** Auxiliary functions for java.lang.System. */
public class System {
    /** Nices the process + io. Only works for Linux. */
    public static boolean fullNice() {
        POSIX posix = POSIXFactory.getNativePOSIX();
        return posix.setpriority(1, 0, 20) == 0;
        //boolean ret = true;
        //if (posix instanceof LinuxPOSIX) {
        //    LinuxPOSIX lp = (LinuxPOSIX)posix;
        //    ret &= lp.setpriority(1, 0, 20) == 0;
        //    ret &= lp.ioprio_set(IOPRIO_WHO_PROCESS, 0,
        //                         IOPRIO_PRIO_VALUE(IOPRIO_CLASS_BE, 7)) == 0;
        //    return ret;
        //} else {
        //    return false;
        //}
    }
}
