"""Manages administration privileges"""
import os

class AdminTracker:
    def __init__(self, secret: str,
                csv_header: str = 'telegram_id,clearance',
                local_dir: str = './local_data',
                admins_file: str = 'admins.txt',
                docker_mode: bool = True) -> None:
        """Manages administration privileges"""
        self.docker_mode = docker_mode
        self.secret = secret if secret != "DISABLED" else None
        self.local_dir = '/data' if self.docker_mode else local_dir
        self.admins_filename = admins_file
        self.admins_file_path = os.path.join(self.local_dir, self.admins_filename)
        self.csv_header = csv_header
        self.admins = {}
        self._ensure_local_dir()
        self._ensure_admins_file()
        self.parse()

    def _ensure_local_dir(self) -> None:
        os.makedirs(self.local_dir, exist_ok=True)
    
    def _ensure_admins_file(self) -> None:
        if not os.path.exists(self.admins_file_path):
            os.mknod(self.admins_file_path)
            with open(self.admins_file_path, 'a') as f:
                f.write(f'{self.csv_header}\n')

    def _write_admins(self) -> None:
        with open(self.admins_file_path, 'w') as f:
            f.write(f'{self.csv_header}\n')
            for admin in self.admins.keys():
                f.write(f'{admin},{self.admins[admin]["clearance"]}\n')
    
    def get_all(self) -> dict:
        return self.admins
    
    def parse(self) -> None:
        with open(self.admins_file_path, 'r') as f:
            lines = f.readlines()
            header_skipped = False
            for line in lines:
                if not header_skipped:
                    header_skipped = True
                    continue
                line = line.split(',')
                line[1] = line[1].split('\n')[0]  # Get rid of newline escaped char
                self.admins[line[0]] = {'clearance': line[1]}
    
    def is_admin(self, name: str) -> bool:
        if name in self.admins.keys():
            return True
        return False

    def get_clearance(self, name: str) -> int:
        """Returns admin's clearance level; -1 if not an admin"""
        if not self.is_admin: return -1
        return self.admins[name]['clearance']
    
    def add(self, name: str, secret: str, clearance: int = 0) -> bool:
        """Adds admin if provided secret is correct
        Returns False if the secret does not match,
        None if the user is already an admin,
        True if the user is now an admin"""
        if secret != self.secret: return False
        if name in self.admins.keys():
            return None
        with open(self.admins_file_path, 'a') as f:
            f.write(f'{name},{clearance}\n')
        self.parse()
        return True

    def remove(self, name: str, secret: str) -> bool:
        if secret != self.secret: return False
        if name not in self.admins.keys(): return True
        new_admins = {}
        for admin in self.admins.keys():
            if admin == name: continue
            new_admins[admin] = self.admins[admin]
        self.admins = new_admins
        self._write_admins()
        return True
