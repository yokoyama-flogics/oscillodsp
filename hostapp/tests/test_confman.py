from confman import *

enable_debug()


class ConfigManagerTestBench:
    def __init__(self):
        import tempfile

        self.__fd = tempfile.NamedTemporaryFile(mode="w")
        self.__fd.write(
            """
comport: pcsim
lastdir: /Users/yokoyama/tmp
loglevels:
- desc: Application
  from: app
  level: 10
- desc: DSP Driver
  from: dspj
  level: 20
chcolors:
- gold
- dodgerblue
- darkred
- darkblue"""
        )

        self.__fd.flush()

        self.__confman = ConfigManager(
            appname="pytest_ConfigManager", appauthor="com.flogics"
        )

    def confman(self):
        return self.__confman

    def fd(self):
        return self.__fd

    def __del__(self):
        import shutil

        shutil.rmtree(self.__confman.confdir)  # XXX  may be dangerous


def test_load1():
    tb = ConfigManagerTestBench()
    tb.confman().load(tb.fd().name)
    assert tb.confman().init[CONFIGFILE] == tb.fd().name


def test_set1():
    tb = ConfigManagerTestBench()
    tb.confman().load(tb.fd().name)
    assert tb.confman().updated() is False

    # if the identical value was set, updated() must still return False
    tb.confman().set("comport", "pcsim")
    assert tb.confman().updated() is False


def test_set2():
    tb = ConfigManagerTestBench()
    tb.confman().load(tb.fd().name)
    assert tb.confman().updated() is False

    chcolors = tb.confman().get("chcolors")

    chcolors[0] = "gold"
    tb.confman().set("chcolors", chcolors)
    assert tb.confman().updated() is False

    chcolors[0] = "blue"
    tb.confman().set("chcolors", chcolors)
    assert tb.confman().updated() is True
