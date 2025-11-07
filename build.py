import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import traceback
from typing import List, Optional

class SevenZip:
    def __init__(self, possibleExecutablePaths: List[str], flagsForSearch: List[str]):
        maybePath = SevenZip.findWorkingExecutablePath(possibleExecutablePaths, flagsForSearch)
        if maybePath is None:
            raise Exception(f"Couldn't find working 7zip executable, tried {possibleExecutablePaths}")

        self.executablePath = maybePath #type: str

    @staticmethod
    def findWorkingExecutablePath(executable_paths, flags):
        #type: (List[str], List[str]) -> Optional[str]
        """
        Try to execute each path in executable_paths to see which one can be called and returns exit code 0
        The 'flags' argument is any extra flags required to make the executable return 0 exit code
        :param executable_paths: a list [] of possible executable paths (eg. "./7za", "7z")
        :param flags: a list [] of any extra flags like "-h" required to make the executable have a 0 exit code
        :return: the path of the valid executable, or None if no valid executables found
        """
        with open(os.devnull, 'w') as os_devnull:
            for path in executable_paths:
                try:
                    if subprocess.call([path] + flags, stdout=os_devnull, stderr=os_devnull) == 0:
                        return path
                except:
                    pass

        return None

    def sevenZipMakeArchive(self, input_path, output_filename):
        tryRemoveTree(output_filename)
        subprocess.call([self.executablePath, "a", output_filename, input_path])

def tryRemoveTree(path):
    attempts = 5
    for i in range(attempts):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return

        except FileNotFoundError:
            return
        except Exception:
            print(f'Warning: Failed to remove "{path}" attempt {i}/{attempts}')
            traceback.print_exc()

        time.sleep(1)

def download(url):
    print(f"Starting download of URL: {url}")
    subprocess.call(['curl', '-OJLf', url])

def clearOldFiles(clearOutput):
    filesToClear = [
        'versionData.json',
        'installData.json',
        'cachedDownloadSizes.json',
    ]

    # Note: need to keep 'updates.json' for compatability with old installers
    # which expect the updates.json in the release
    # Can be removed once it is unlikely people are using the old installer
    if clearOutput:
        filesToClear.extend(['installerMetaData.zip', 'updates.json'])

    for file in filesToClear:
        tryRemoveTree(file)

# Remove old files
clearOldFiles(clearOutput = True)

# Look for 7zip executable
sevenZip = SevenZip(["7za", "7z"], ['-h'])

# Build updates.json file
# This contains some html which is displayed in the installer, so we can update the installer html without building a new installer release.
# For example, for writing news about updates etc.

out_json_path = 'updates.json'

combined = {}


for file in Path('.').glob('*.html'):
    with open(file, encoding='utf-8') as f:
        all_html = f.read()

    name = file.stem

    combined[name] = {
        'status': all_html
    }


with open(out_json_path, 'w', encoding="utf-8") as file:
    json.dump(combined, file)

## Download installData.json etc.
download("https://github.com/07th-mod/python-patcher/raw/refs/heads/master/versionData.json")
download("https://github.com/07th-mod/python-patcher/raw/refs/heads/master/installData.json")
download("https://github.com/07th-mod/python-patcher/raw/refs/heads/master/cachedDownloadSizes.json")

## Zip the json files into an archive
sevenZip.sevenZipMakeArchive('*.json', "installerMetaData.zip")

# Cleanup after script finished - may want to disable this when debugging
clearOldFiles(clearOutput = False)
