
import moegodot_build_utilities as util
import moegodot_build_utilities.detector as detector
import logging

util.setup()

log = logging.getLogger(__file__)

log.debug("this is a test invoker")

info = detector.SystemInformation(__file__)

info.install_package_in_unix({ })
info.use_tool("node", ">=21.0.0")


