import os
import subprocess
import docker
import yaml
from raincloud.rainstick.config import app_config


class Service(object):
    def __init__(self, name):
        self.name = name
        self.status = self.get_status()
        self.settings = self.get_settings()
        self.needs_update = self.check_needs_update()

    @classmethod
    def all(cls):
        return [Service(folder) for folder in cls.all_folders()]

    @classmethod
    def all_folders(cls):
        return [ f.name for f in os.scandir(cls.__services_folder()) if f.is_dir() ]

    def enable(self):
        if not self.__is_installed():
            install_script = "{0}/install.sh".format(self.__service_folder())
            if os.path.isfile(install_script):
                output = subprocess.check_output("bash {0}".format(install_script), shell=True, env=app_config)
        self.update_env()
        command = "{0} up -d".format(self.__docker_command())
        output = self.__run_command(command)
        self.set_status()
        # set flag since any new variables were applied
        self.set_needs_update(False)
        return output

    def disable(self):
        command = "{0} down".format(self.__docker_command())
        output = self.__run_command(command)
        self.set_status()

        return output

    def set_status(self):
        self.status = self.get_status()

    def get_status(self):
        client = docker.from_env()
        try:
            if client.containers.get(self.name).status == 'running':
                return 'enabled'
            else:
                return 'disabled'
        except docker.errors.NotFound:
            return 'disabled'

    def get_settings(self):
        service_file = self.get_service_file()
        env = self.__get_env_dict()
        if os.path.isfile(service_file):
            with open(service_file) as f:
                settings = yaml.safe_load(f)
                var_fields_with_values = []
                # Parse field values from .env
                for var in settings['var_fields']:
                    try:
                        var['value'] = env[var['name']]
                    except:
                        pass
                    var_fields_with_values.append(var)
                settings['var_fields'] = var_fields_with_values
                return settings
        return {}

    def get_service_file(self):
        return "{0}/service.yml".format(self.__service_folder())

    def get_env_file(self):
        return "{0}/.env".format(self.__data_folder())

    def get_update_file(self):
        return "{0}/.update".format(self.__data_folder())



    def update_env(self, variable=False):
         # update the .env with new default values
         # preserve existing values
         # replace values of variable if passed
         env = self.__get_env_dict()
         if variable:
             env[variable['name']] = variable['value']
         for var in self.settings['var_fields']:
             if var['name'] not in env:
                 env[var['name']] = var['default']
         self.__save_env(env)

    def update_var(self, variable):
        if self.status == 'enabled':
            self.set_needs_update(True)
        self.update_env(variable)
        self.settings = self.get_settings()
        return self.__dict__

    def check_needs_update(self):
        return os.path.isfile(self.get_update_file())

    def set_needs_update(self, needs_update):
        self.needs_update = needs_update
        update_file = self.get_update_file()
        if needs_update:
            with open(update_file, 'w') as f:
                pass
        else:
            if os.path.isfile(update_file):
                os.remove(update_file)
            else:
                print("Update flag unset. Skipping...")

    @classmethod
    def __services_folder(cls):
        base_dir = os.getcwd()

        return os.path.join(base_dir, 'services')

    def __data_folder(self):

        return os.path.join(app_config['path_to_service_data'], self.name)

    def __is_installed(self):

        return os.path.isdir(self.__data_folder())

    def __run_command(self, command):
        if self.name not in Service.all_folders():
            raise Exception('Service not enabled')

        return subprocess.check_output(command, shell=True)

    def __get_env_dict(self):
        env_file = self.get_env_file()
        dict = {}
        if os.path.isfile(env_file):
            vars = open(env_file, "r").readlines()
            for assignment in vars:
                name, value = assignment.split("=")
                dict[name] = value.strip()
        return dict

    def __save_env(self, dict):
        env_file = self.get_env_file()
        if not os.path.exists(self.__data_folder()):
            os.makedirs(self.__data_folder())
        with open(env_file, 'w') as f:
            for name in dict.keys():
                assignment = "{0}={1}\n".format(name, dict[name])
                f.write(assignment)

    def __service_folder(self):
        return os.path.join(Service.__services_folder(), self.name)

    def __docker_command(self):
        return "docker-compose -f {0}/docker-compose.yml --env-file {1}/.env ".format(self.__service_folder(), self.__data_folder())
