import os
from glob import glob
from typing import List

def ls_files_by_pattern(src: str, 
                        pattern: str) -> List[str]:
    """Mimics $ ls /path/to/src/*[pattern] functionality."""

    fullpaths=os.path.join(src, "*"+pattern)
    ls=list(glob(fullpaths))

    return sorted(ls)


def load_file_data(file: str) -> List[str] | None:
    """Load lines from file to string buffer."""

    with open(file, encoding='ascii') as f:
        try:
            lines = f.readlines()
        except UnicodeDecodeError as err:
            print(f"UnicodeDecodeError when reading file: {f}")
            return None
        
    return lines