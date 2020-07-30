import math

def get_ftdi_rates(min):
    CLOCK = 3e6
    DIV_SUB = sorted([0.0, 0.5, 0.25, 0.125])

    result = []

    until = CLOCK / min
    # print("until:", until)

    for div_int in range(1, int(math.ceil(until)) + 1):
        for div_sub in DIV_SUB:
            div = div_int + div_sub
            rate = CLOCK / div
            if (rate >= min):
                result.append(rate)
                # print('{:}: {:}'.format(div, CLOCK / div))

    return result


def get_ti_rates(min):
    CLOCK = 1e9 / 6
    DIV_PRE = sorted([13, 16])

    result = []

    until = CLOCK / min / DIV_PRE[0]
    # print("until:", until)

    for div_main in range(1, int(math.ceil(until)) + 1):
        for div_pre in DIV_PRE:
            div = div_main * div_pre
            rate = CLOCK / div
            if (rate >= min):
                result.append(rate)
                # print('{:}: {:}'.format(div, CLOCK / div))

    return result


MIN = 400e3
ftdi_set = get_ftdi_rates(MIN)
ti_set = get_ti_rates(MIN)

result = []

for ftdi in ftdi_set:
    for ti in ti_set:
        result.append((ftdi, ti, abs(ftdi / ti - 1)))

for cand in result:
    if cand[2] < 0.03:
        print("{:} {:} {:}".format(cand[0], cand[1], cand[2]))
