import configparser

class ConfigHandler:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        # Load the configuration file
        try:
            self.config.read(self.config_file)
        except FileNotFoundError:
            print(f"Configuration file {self.config_file} not found.")
        except Exception as e:
            print(f"Error reading config file: {e}")

    def get_setting(self, section, key):
        # Retrieve a specific setting
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            print(f"Error retrieving setting [{section}][{key}]: {e}")
            return None