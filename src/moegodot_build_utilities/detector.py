
import logging
import moegodot_build_utilities
from typing import List, Optional
from enum import Enum
import semver

log = logging.getLogger(__file__)

class Architecture(Enum):
    X86 = 1
    X64 = 2
    AArch64 = 3

class Os(Enum):
    Win = 1
    Linux = 2
    MacOS = 3

class PkgMgr(Enum):
    Brew = 1
    Apt = 2
    Pacman = 3

def detect_architect(machine:str) -> Optional[moegodot_build_utilities.Architecture] :
    machine = machine.lower()
    machine.replace('-','_')

    if machine.startswith("i386") or machine.startswith("i586") or machine.startswith("i686") or \
        (machine.startswith("x86") and "64" not in machine): # in case of x86_64
        return Architecture.X86
    elif machine.startswith("amd64") or machine == "x86_64" or machine.startswith("intel64") or machine.startswith("x64"):
        return Architecture.X64
    elif machine.startswith("arm64") or machine.startswith("aarch64"):
        return Architecture.AArch64
    else:
        return None
    
def detect_os(os:str) -> Optional[moegodot_build_utilities.Os] :
    os = os.lower()

    if "windows" in os:
        return Os.Win
    elif "linux" in os:
        return Os.Linux
    elif "darwin" in os:
        return Os.MacOS
    elif "unix" in os:
        return Os.Linux
    elif "win" in os:
        return Os.Win
    elif "mac" in os:
        return Os.MacOS
    else:
        return None
    
def detect_version(ver:str) -> semver.Version:
    parts = ver.split()

    for part in parts:
        origin_part = part
        part = part.strip().strip('v.').strip('V.').strip('v').strip('V.')

        if len(part) > 2 and part[0].isdigit() and "." in part and semver.Version.is_valid(part):
            result = semver.Version.parse(part)
            log.debug(f"Detect version {result} from `{origin_part}`")
            return result
        
    return None


import platform
import os as py_os
import os.path as path
from typing import Dict
from rich import print
from rich.table import Table
from rich.columns import Columns
import subprocess
import shutil

class SystemInformation:
    initial_file: str
    root_dir : str
    os: Os
    arch: Architecture
    environments: Dict[str,str]
    path_env_separator: str

    def __init__(self, initial_file:str, root_dir: str = None, \
                 root_from_parent = False,default_env:Dict[str,str] = None):
        self.initial_file = initial_file

        if root_dir is None:
            root_dir = path.dirname(path.abspath(initial_file))

            if root_from_parent:
                root_dir = path.abspath(f"{root_dir}/../")

        self.root_dir = root_dir

        os = platform.system()
        self.os = detect_os(os)

        arch = platform.machine()
        self.arch = detect_architect(arch)

        if default_env is None:
            default_env = dict(py_os.environ)
        
        self.environments = default_env

        log.info(f"Create SystemInformation in {root_dir}")
        log.info(f"Detect - {self.Os} from platform.system():{os}")
        log.info(f"Detect - {self.arch} from platform.machine():{arch}")

        self.path_env_separator = py_os.pathsep

        log.info(f"Use separator `{self.path_env_separator}` in env:PATH")
        log.info(f"Use environment variables: {self.environments}")
        
        table = Table(title="Environment Variables", show_lines = True)
        table.add_column("Key", justify="center", style="cyan", no_wrap=True, overflow="fold")
        table.add_column("Value", justify="right", style="cyan", no_wrap=True, overflow="fold")

        for key in self.environments.keys():
            if key == "PATH":
                table.add_row(key, 
                              Columns(self.environments[key].split(self.path_env_separator),
                                      align="left",column_first=True, equal=True, expand=True))
            else:
                table.add_row(key, self.environments[key])
        
        print(table)

    def try_get_version_of(self,program:str,arg:str) -> Optional[semver.Version]:
        ran = subprocess.run([program, arg], cwd=self.root_dir, env=self.environments, 
                             check=False, capture_output=True,
                             encoding="utf-8")

        v = detect_version(ran.stdout)

        if v is None:
            v = detect_version(ran.stderr)

        return v

    def get_version_of(self,program:str) -> semver.Version:
        for tried_arg in ["--version","-v","/v","/?"]:
            result = self.try_get_version_of(program, tried_arg)
            if result is not None:
                log.debug(f"Get version `{result}` of `{program}` from argument `{tried_arg}`")
                return result
        raise RuntimeError(f"failed to detected ")

    def find_tool(self,program:str, *ver_matches: List[str]) -> str:
        program = shutil.which(program, path = self.environments["PATH"])

        if program is None:
            raise RuntimeError(f"failed to find program `{program}` in PATH `{self.environments["PATH"]}`")
        
        if len(ver_matches) != 0:
            program_ver = self.get_version_of(program)
        
        for ver_match in ver_matches:
            if not program_ver.match(str(ver_match)):
                raise RuntimeError(f"the program `{program}` with version `{program_ver}` do not match `{ver_match}`")
            
        return program
    
    def use_tool(self,program:str, *ver_matches: List[str]) -> None:
        found = self.find_tool(program,*ver_matches)
        log.info(f"Use tool {found}")
        self.add_env_path(path.dirname(found))

    def add_env_path(self,path:str):
        log.info(f"Add `{path}` to self.environments")
        self.environments["PATH"] = [path] + self.environments["PATH"].split(self.path_env_separator)
    
    def clone_repo(self,url:str,to:str,git_args:List[str] = ["--depth=1"]):
        subprocess.run(["git", "clone", url, to] + git_args, check=True, cwd=self.root_dir,env=self.environments)
    
    def install_package_in_unix(self,switch:Dict[PkgMgr,str],sudo=True):
        if self.os == Os.Win:
            return

        apt = shutil.which("apt-get", path = self.environments["PATH"])
        brew = shutil.which("brew", path = self.environments["PATH"])
        pacman = shutil.which("pacman", path = self.environments["PATH"])

        if sudo:
            sudo = ["sudo"]
        else:
            sudo = []

        if apt is not None:
            subprocess.run(sudo + [apt, "install", switch[PkgMgr.Apt]],check=True)
        elif brew is not None:
            subprocess.run(sudo + [brew, "install", switch[PkgMgr.Brew]],check=True)
        elif pacman is not None:
            subprocess.run(sudo + [pacman, "-S", switch[PkgMgr.Pacman]],check=True)
