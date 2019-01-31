from typing import List

class PatchSet:
  def __init__(self, diff: str) -> None: ...
  modified_files: List[PatchedFile]
  added_files: List[PatchedFile]
  removed_files: List[PatchedFile]

class PatchedFile:
  path: str
  


  
