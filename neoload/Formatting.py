import datetime

def printNiceTimeDelta(stime, etime):
    return printNiceTime(etime - stime)

def printNiceTime(total_seconds):
    delay = datetime.timedelta(seconds=total_seconds)
    if (delay.days > 0):
        out = str(delay).replace(" days, ", ":")
    else:
        out = "0:" + str(delay)
    outAr = out.split(':')
    outAr = ["%02d" % (int(float(x))) for x in outAr]
    out   = ":".join(outAr)
    while out.startswith("00:"):
        out = out.replace("00:","",1)
    return out
