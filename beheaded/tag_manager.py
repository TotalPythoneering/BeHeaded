# MISSION: Create a NamedDict storage system.
# STATUS: Testing
# VERSION: 0.1.0
# NOTES: Using NamedDict as the data-model for this controller.
# DATE: 2026-01-21 20:53:56
# FILE: tag_manager.py
# AUTHOR: Randall Nagy
#
import os, sys, shutil
import json
from pathlib import Path
from named_dict import NamedDict
from storage_file import StorageManager

class TagManager:
    """ Manage user-named dictionaries in a database in a specific folder. """ 
    def __init__(self, app_name, folder_path=None):
        """ Instance a TagManager for a folder path. Folder need not exist. """ 
        self.user_path = Path.home() / app_name
        self.user_path.mkdir(parents=True, exist_ok=True)
        if not folder_path:
            folder_path = self.user_path
        self.folder_path = Path(folder_path).resolve()
        self.escape = '.!' # special 'ops token
        self.dba = StorageManager(app_name, self.folder_path) # driver

    def destroy_app_folder(self)->bool:
        """ Remove the app folder and all it contains. """
        if os.path.exists(self.user_path):
            try:
                shutil.rmtree(self.user_path)
                return True
            except OSError as e:
                pass
        return False

    def get_app_folder(self):
        """ Return the location of the application folder. """ 
        return str(self.user_path)

    def check_folder_exists(self):
        """ Check if the folder path exists. """ 
        return self.folder_path.is_dir()

    def create_folder_if_not_exists(self):
        """ Create the folder if it does not exist. """ 
        if not self.check_folder_exists():
            self.folder_path.mkdir(parents=True, exist_ok=True)

    def exe_create_set(self, name, data=None):
        """ Create a new Collection (named dictionary). Loops to collect data when none. """
        if not name:
            print('Collection name is invalid..')
            return
        if self.dba.exists(name):
            print(f'Collection [{name}] already exists.')
            return
        if not data:
            data = {}
            while True:
                self.show_dict(data)
                key = input("Enter key: ").strip()
                if not key:
                    break
                value = input(f"Value for {key}: ").strip()
                data[key] = value
        if self.dba.create(name, data):
            print(f"Created collection '{name}'")
            return True
        return False

    def show_dict(self, a_dict):
        ''' Line a dictionary to the screen. '''
        if not a_dict:
            print("{}")
            return
        if isinstance(a_dict, NamedDict):
            a_dict = a_dict.data
        if not isinstance(a_dict, dict):
            print("{}")
            return
        for key in a_dict:
            print(f"{key} : {a_dict[key]}")
        print()


    def _edit_keys(self, data:dict)->dict:
        print("~~~ Key Editor ~~~")
        keys = list(data.keys())
        for ss, key in enumerate(keys,1):
            print(f'{ss}.) {key}')
        which = input("# to change: ").strip()
        try:
            which = int(which)
            which -= 1
            okey = keys[which]
            oval = data[okey]
            new_key = input(f'Rename "{okey}" to: ').strip()
            if new_key:
                del data[okey]
                data[new_key] = oval
                print(f'"{new_key}" = "{data[new_key]}"')
            else:
                option = input("Delete everything for '{okey}'? (y/N) ").strip().lower()
                if option and option[0] == 'y':
                    del data[okey]
                    print(f'"{okey}" and "{oval}" removed.')
                else:
                    print("... unchanged ...")
        except Exception as ex:
            print(ex)
            print(" ... ignored ...")
        return data
    
    def edit_keyes(self, named_dict:NamedDict)->NamedDict:
        if not isinstance(named_dict, NamedDict):
            return NamedDict() # gigo
        if named_dict.data == None:
            named_dict.data = dict()
        named_dict.data = self._edit_keys(named_dict.data)
        return named_dict    

    def exe_read_set(self, name):
        """ Read a named dictionary (a.k.a 'collection') data. """
        if not name:
            print('no data.')
            return
        if self.dba.exists(name):
            print(f'not found.')
            return
        return self.dba.read(name)   

    def exe_update_set(self, name)->bool:
        ''' Dynamic dictionary update loop. '''
        if not name:
            print('no data.')
            return
        if self.dba.exists(name):
            print(f'not found.')
            return
        named_dict = self.exe_read_set(name)
        if not named_dict:
            return False
        
        while True:
            print(f"Editing values. Enter blank key to update Collection '{name}'.")
            self.show_dict(named_dict)
            print(f"Enter {self.escape} to manage Keys.")
            key_input = input("Add/update Key: ").strip()
            if not key_input:
                break
            if key_input == self.escape:
                named_dict = self.edit_keys(named_dict)
                continue
            
            value_input = input("New Value: ").strip()
            named_dict.data[key_input] = value_input

        if named_dict is not None:
            if self.dba.update(named_dict):
                print(f"Updated Collection '{name}'.")
            else:
                print(f"Unable to update '{name}'.")

    def exe_delete_set(self, name):
        """ Delete a named collection. """
        if not name:
            print('no data.')
            return
        if self.dba.exists(name):
            print(f'not found.')
            return
        if self.dba.delete(name):
            print(f"Deleted collection: '{name}'")
            return True
        else:
            print(f"Error: Collection '{name}' not found.")
            return False

    def exe_list(self):
        """ Display collection list. """
        rows = self.dba.list()
        if rows:
            print("Collection:")
            for ss, f in enumerate(rows, 1):
                print(f"{ss}) {f}")

    def do_create(self, **kwargs):
        ''' Create a new named collection. '''
        name = input("Enter collection name: ").strip()
        self.exe_create_set(name)
    
    def do_read(self, **kwargs):
        ''' Show Collection content. '''
        name = input("Enter Collection name to read: ").strip()
        self.show_dict(self.exe_read_set(name))
    
    def do_update(self, **kwargs):
        ''' Update Collection content. '''
        name = input("Enter name to update: ").strip()
        self.exe_update_set(name)
    
    def do_delete(self, **kwargs):
        ''' Delete a collection. '''
        name = input("Enter name to delete: ").strip()
        self.exe_delete_set(name)
    
    def do_list(self, **kwargs):
        ''' List all collections. '''
        self.exe_list()
    
    def do_report(self, **kwargs):
        ''' List all Collection content. '''
        rows = self.dba.list()
        if rows:
            print("*** Collection Report ***\n")
            for a_set in rows:
                print(f"Collection: [{a_set}]")
                data = self.exe_read_set(a_set)
                self.show_dict(data)
        else:
            print(f"No data in {self.folder_path}.")    
    
    def do_quit(self, **kwargs):
        ''' Quit the interface manager. '''
        sys.exit(0)

    def mainloop(self):
        """ Provide a basic interactive TUI for managing named dictionaries. """ 
        print(f"\n--- Tag Manager TUI ---")
        print(f"Managing folder: {self.folder_path}")
        self.create_folder_if_not_exists()
        self.exe_list()
        options = {
            'Create':self.do_create,
            'Read':self.do_read,
            'Update':self.do_update,
            'Delete':self.do_delete,
            'List':self.do_list,
            'Report':self.do_report,
            'Quit':self.do_quit
            }
        keys = list(options.keys())
        times=0
        while True:
            print();selection = None
            for ss, op in enumerate(keys, 1):
                print(f'{ss}.) {op}:\t{options[op].__doc__}')
            try:
                selection = input("Enter #: ")
                which = int(selection.strip())
                if which > 0 and which <= len(keys):
                    times = 0
                    selection = keys[which-1]
                    if selection in options: # double check
                        print('*'*which, selection)
                        options[selection]()
                else:
                    print(f"Invalid number {which}.")
            except Exception as ex:
                times += 1
                if times > 12:
                    print("I've no time for this - bye!")
                    sys.exit(1001)
                print(ex)
                print("Numbers only, please.")
                continue


if __name__ == '__main__':
    sut = TagManager("~TagManager9K")
    sut.mainloop()
##    if sut.destroy_app_folder():
##        print(f"{sut.user_path} removed.")
    
