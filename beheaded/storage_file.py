# MISSION: Create a reusable NamedDict 'database' driver.
# STATUS: Testing
# VERSION: 0.1.0
# NOTES: NamedDict = 'file in directory' / JSON file driver.
# DATE: 2026-01-21 20:49:01
# FILE: storage_file.py
# AUTHOR: Randall Nagy
#
import os, sys, os.path
sys.path.append('..')
import shutil, json
from pathlib import Path

from beheaded.named_dict import NamedDict

class StorageManager:

    def __init__(self, app_name, folder_path=None):
        """ Instance a TagManager for a folder path. Folder need not exist. """ 
        self.user_path = Path.home() / app_name
        self.user_path.mkdir(parents=True, exist_ok=True)
        if not folder_path:
            folder_path = self.user_path
        self.folder_path = Path(folder_path).resolve()

    def destroy(self, empty=False)->bool:
        '''
        Attempt to remove the 'app data folder.
        Use `empty` to delete any JSON files.
        NOTE: USING `empty` DELETES ONLY THE .JSON FILES.
        Returns False if 'app folder is not able to be removed.
        '''
        if empty:
            for node in self.list():
                self.delete(node)
        if self.folder_path.exists():
            # The directory must be empty:
            self.folder_path.rmdir() 
            return not self.folder_path.exists()
        return True # gigo

    def _get_file_path(self, name):
        """ Get the full file path for a file name. """
        if name.endswith('.json'):
            return self.folder_path / name
        return self.folder_path / f"{name}.json"

    def exists(self, name:str)->bool:
        ''' See if the data's name already exists. '''
        if not name:
            return False
        return self._get_file_path(name).exists()
           
    def create(self, name, data)->NamedDict:
        '''
        Create a new JSON file.
        Updates content if has already been created.
        '''
        if not name:
            return None
        if not data:
            data = {}
        file_path = self._get_file_path(name)
        if file_path.exists():
            if not self.update(NamedDict.Create(name, data)):
                raise IOError(f"Error: File {file_path} access error.")
        else:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
        return self.read(name)

    def read(self, an_obj)->NamedDict:
        ''' Read the tag set associated with the name. None on error. '''
        if not an_obj:
            return None
        if isinstance(an_obj, NamedDict):
            an_obj = an_obj.name
        file_path = self._get_file_path(an_obj)
        if file_path.exists():
            fh = open(file_path, 'r')
            data = json.load(fh)
            fh.close()
            return NamedDict.Create(an_obj, data)
        return NamedDict()

    def update(self, named_dict:NamedDict)->bool:
        ''' Replace the named tag set. False if file not updated.'''
        if not named_dict:
            return False
        if not isinstance(named_dict, NamedDict):
            return False
        file_path = self._get_file_path(named_dict.name)
        if named_dict.data == None:
            named_dict.data = dict()
        with open(file_path, 'w') as f:
            json.dump(named_dict.data, f, indent=4)
        return file_path.exists()

    def delete(self, obj)->bool:
        ''' Delete all key value pairs for the name.
            return False if unable to delete the tag set.
        '''
        if not obj:
            return True
        name = str(obj)
        if isinstance(obj, NamedDict):
            name = obj.name
        file_path = self._get_file_path(name)
        if not file_path.exists():
            return True
        file_path.unlink()
        return not file_path.exists()

    def list(self)->list:
        ''' Get the name[s] of the collections, if any. '''
        results = []
        for json in self._list_files():
            results.append(json.replace('.json',''))
        return results
    
    def _list_files(self)->list:
        """ List the names of all user created named-dictionaries (files.) """ 
        files = self.folder_path.glob("*.json")
        return [file.stem for file in files]


if __name__ == '__main__':
    # Basic test cases
    import sys
    sut = StorageManager('~test.StorageManager')
    print(f'Testing [{sut.folder_path}]')
    row = sut.create('testA', dict())
    if not row:
        print('Error 10001: File creation error.')
        sys.exit(9)
    if row.is_null():
        print(row.name)
        print('Error 10010: File creation error.')
        sys.exit(9)
    row = sut.read('testA')
    if not row:
        print('Error 10030: File read error.')
        sys.exit(9)
    if row.is_null():
        print('Error 10040: File read error.')
        sys.exit(9)

    row.data['one'] = 1
    row.data['two'] = 2
    row.data['three'] = 3
    if not sut.update(row):
        print('Error: Update.')
    row2 = sut.read(row.name)
    if row != row2:
        print("Error 10050: Equality error.")
        sys.exit(9)
    if not row:
        print('Error 10060: File update error.')
        sys.exit(9)
    if row.is_null():
        print('Error 10070: File update error.')
        sys.exit(9)
    if not sut.delete(row):
        print('Error 10080: Unable to remove file.')
        sys.exit(9)
    if len(sut._list_files()):
        print('Error 10090: Unable to destroy file.')
        sys.exit(9)
    if not sut.destroy():
        print('Error 10100: Unable to unlink nexus.')
        sys.exit(9)
    print("Testing Success")
    sys.exit(0)
    

