# MISSION: Create an independant tag file manager.
# STATUS: Testing
# VERSION: 0.0.0
# NOTES: A nice database for simple data.
# DATE: 2026-01-19 03:09:25
# FILE: tag_manager.py
# AUTHOR: Randall Nagy
#
import os, shutil
import json
from pathlib import Path


class TagManager:
    """ Manage user-named dictionaries as JSON files in a specified folder. """ 

    def __init__(self, app_name, folder_path=None):
        """ Instance a TagManager for a folder path. Folder need not exist. """ 
        self.user_path = Path.home() / app_name
        self.user_path.mkdir(parents=True, exist_ok=True)
        if not folder_path:
            folder_path = self.user_path
        self.folder_path = Path(folder_path).resolve()
        self.escape = '.!' # special 'ops token

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

    def _get_file_path(self, name):
        """ Helper to get the full file path for a file name. """
        if name.endswith('.json'):
            return self.folder_path / name
        return self.folder_path / f"{name}.json"

    def exe_create_file(self, name, data=None):
        """ Create a new file (JSON file). Loops to collect data when none. """
        if not name:
            print('no file.')
            return
        file_path = self._get_file_path(name)
        if file_path.exists():
            print(f"Error: file '{name}' already exists.")
            return False
        if not data:
            data = {}
            while True:
                self.show_dict(data)
                key = input("Enter key: ").strip()
                if not key:
                    break
                value = input(f"Value for {key}: ").strip()
                data[key] = value
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Created file: '{name}'")
        return True

    def show_dict(self, a_dict):
        ''' Line a dictionary to the screen. '''
        if not a_dict:
            print("{}")
        else:
            for key in a_dict:
                print(f"{key} : {a_dict[key]}")
        print()

    def exe_read_file(self, name):
        """ Read a file (JSON file) data. """
        if not name:
            print('no file.')
            return
        file_path = self._get_file_path(name)
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        else:
            print(f"Error: file '{name}' not found.")
            return None

    def edit_keys(self, data:dict)->dict:
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

    def exe_update_file(self, name)->bool:
        ''' Dynamic dictionary update loop. '''
        if not name:
            print('no file.')
            return
        data = self.exe_read_file(name)
        if not data:
            return self.exe_create_file() # meh

        while True:
            print(f"Editing values. Enter blank key to update file '{name}'.")
            self.show_dict(data)
            print(f"Enter {self.escape} to manage Keys.")
            key_input = input("Add/update Key: ").strip()
            if not key_input:
                break
            if key_input == self.escape:
                data = self.edit_keys(data)
                continue
            
            value_input = input("New Value: ").strip()
            data[key_input] = value_input

        if data is not None:
            with open(self._get_file_path(name), 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Updated file '{name}'.")

    def exe_delete_file(self, name):
        """ Delete a file (JSON file). """
        if not name:
            print('no file.')
            return
        file_path = self._get_file_path(name)
        if file_path.exists():
            file_path.unlink()
            print(f"Deleted file: '{name}'")
            return True
        else:
            print(f"Error: file '{name}' not found.")
            return False

    def get_json_files(self):
        """ List the names of all user created JSON files. """ 
        files = self.folder_path.glob("*.json")
        return [file.stem for file in files]

    def exe_list(self):
        """ Display the list of files. """
        files = self.get_json_files()
        if files:
            print("Available:")
            for ss, f in enumerate(files, 1):
                print(f"{ss}) {f}")
        else:
            print(f"No files in {self.folder_path}.")

    def do_create(self, **kwargs):
        ''' Create a new data file. '''
        name = input("Enter file name: ").strip()
        self.exe_create_file(name)
    
    def do_read(self, **kwargs):
        ''' Show file content. '''
        name = input("Enter file name to read: ").strip()
        self.show_dict(self.exe_read_file(name))
    
    def do_update(self, **kwargs):
        ''' Update file content. '''
        name = input("Enter file name to update: ").strip()
        self.exe_update_file(name)
    
    def do_delete(self, **kwargs):
        ''' Delete a file. '''
        name = input("Enter file name to delete: ").strip()
        self.exe_delete_file(name)
    
    def do_list(self, **kwargs):
        ''' List all files. '''
        self.exe_list()
    
    def do_report(self, **kwargs):
        ''' List all file content. '''
        files = self.get_json_files()
        if files:
            print("*** File Report ***\n")
            for a_file in files:
                print(f"File: [{a_file}]")
                data = self.exe_read_file(a_file)
                self.show_dict(data)
        else:
            print(f"No files in {self.folder_path}.")    
    
    def do_quit(self, **kwargs):
        ''' Quit the interface manager. '''
        exit(0)

    def mainloop(self):
        """ Provide a basic interactive TUI for managing json files in the folder. """ 
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
                    exit(1001)
                print(ex)
                print("Numbers only, please.")
                continue


if __name__ == '__main__':
    sut = TagManager("~TagManager9000")
    sut.mainloop()
##    if sut.destroy_app_folder():
##        print(f"{sut.user_path} removed.")
    
