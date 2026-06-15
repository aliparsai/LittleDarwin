#!/usr/bin/env python3
import sys
import time
import datetime
from mediumdarwin.Schemata import parseCmdArgs
from optparse import OptionParser


def main(args):
    s_time = time.time()
    optionParser = OptionParser()
    options, filterType, filterList, higherOrder = parseCmdArgs(
        optionParser, args
    )
    if (options.reset):
        from mediumdarwin.Schemata import Schemata
        schemata = Schemata(mockArgs=args)
        schemata.cleanup_mediumDarwin()
    else:
        from mediumdarwin.Schemata import Schemata
        schemata = Schemata(mockArgs=args)
        try:
            if options.isSchemataActive:
                schemata.main()
            else:
                from mediumdarwin.MediumDarwin import MediumDarwin
                mediumDarwin = MediumDarwin()
                mediumDarwin.main(mockArgs=args)
        finally:
            schemata.cleanup_mediumDarwin()

    print("elapsed: " + str(datetime.timedelta(seconds=int(time.time() - s_time))))
    return 0


if __name__ == "__main__":
    main(sys.argv)
