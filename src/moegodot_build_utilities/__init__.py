
import sys
import logging
from rich.logging import RichHandler
from rich.traceback import install
from importlib.metadata import version, requires

log = logging.getLogger(__file__)

package_name = "moegodot_build_utilities"
package_version = version(package_name)
package_requires = requires(package_name)

def print_package_information():
    log.info(f"Moegodot's build utility version: {package_version}")
    log.info("Moegodot's build utility dependencies: ")
    if package_requires:
        for requires in package_requires:
            log.info(f" - {requires}")
    else:
        log.warning("Failed to find dependencies")

def setup(setup_logging = True,setup_traceback = True):
    if setup_traceback:
        install(show_locals=True, max_frames=0)

    if setup_logging:
        logging.basicConfig(
            level="NOTSET", format="%(message)s", datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)]
        )

    print_package_information()
    
if __name__ == "__main__":
    setup()
    log.info("Moegodot-build-utilities is a toolset that help you construct a brave new world when develop software!")
    log.fatal("Moegodot-build-utilities can only be used as a library!")
    sys.exit(1)
