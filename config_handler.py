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

    def get_token(self):
        return self.get_setting('DEFAULT', 'Token')

    def get_api_endpoint(self):
        return self.get_setting('DEFAULT', 'APIEndpoint')
    
    def get_api_key(self):
        return self.get_setting('DEFAULT', 'API_Key')

    def get_wait_time(self):
        return int(self.get_setting('DEFAULT', 'WaitTime'))

    def get_channel_id(self, channel_name):
        return int(self.get_setting('CHANNELS', channel_name))

    def get_setting(self, section, key):
        # Retrieve a specific setting
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            print(f"Error retrieving setting [{section}][{key}]: {e}")
            return None
        
# Example usage
if __name__ == "__main__":
    config_handler = ConfigHandler()
    print(config_handler.get_token())