from .httpclient import post, get
import time
import os
import json

token = None
# Path for storing instance name mappings
INSTANCE_NAMES_FILE = os.path.expanduser("~/.jarvislabs/instance_names.json")

# Ensure directory exists
os.makedirs(os.path.dirname(INSTANCE_NAMES_FILE), exist_ok=True)

# Dictionary to store instance ID -> custom name mappings
instance_names = {}

def load_instance_names():
    """Load saved instance names from file."""
    global instance_names
    try:
        if os.path.exists(INSTANCE_NAMES_FILE):
            with open(INSTANCE_NAMES_FILE, 'r') as f:
                instance_names = json.load(f)
    except Exception:
        # If loading fails, start with empty dict
        instance_names = {}
    return instance_names

def save_instance_name(machine_id, name):
    """Save instance name to persistent storage."""
    global instance_names
    if not machine_id:
        return
    
    # Load current names
    load_instance_names()
    
    # Update with new name
    instance_names[str(machine_id)] = name
    
    try:
        # Save to file
        with open(INSTANCE_NAMES_FILE, 'w') as f:
            json.dump(instance_names, f)
    except Exception:
        # If saving fails, continue without error
        pass

def get_instance_name(machine_id):
    """Get custom name for an instance if it exists."""
    if not instance_names:
        load_instance_names()
    return instance_names.get(str(machine_id))

class Instance(object):
    def __init__(self,
                 hdd: int,
                 gpu_type: str,
                 machine_id: int,
                 num_gpus: int = None,
                 num_cpus: int = None,
                 name: str = '',
                 script_id: str = '',
                 is_reserved: bool = True,
                 url: str = '',
                 status: str = '',
                 ssh_str: str = '',
                 endpoints: str = '',
                 duration: str = 'hour',
                 script_args: str = '',
                 http_ports: str = '',
                 template: str = ''
                 ):
        
        self.gpu_type = gpu_type
        self.num_gpus = num_gpus
        self.num_cpus = num_cpus
        self.hdd = hdd
        self.name = name
        self.machine_id = machine_id
        self.script_id = script_id
        self.is_reserved = is_reserved
        self.duration = duration
        self.script_args = script_args
        self.http_ports = http_ports
        self.template = template
        self.url = url
        self.endpoints = endpoints
        self.ssh_str = ssh_str
        self.status = status

    def pause(self):
        '''
        Pause the running machine.
        Returns:
            status: Returns the pause status of the machine --> success or failed.
        '''
        pause_response = post({},f'misc/pause', 
                              token,
                              query_params={'machine_id':f'{self.machine_id}'})
        if pause_response['success']:
            self.status = 'Paused'
        return pause_response
    
    def destroy(self):
        '''
        Destroy the running or paused machine. 
        Returns:
            status:  Returns the destroy status of the machine --> success or failed.
        '''
        destroy_response = post({},
                                f'misc/destroy',
                                token,
                                query_params={'machine_id': self.machine_id})
        if destroy_response['success']:
            self.status = 'Destroyed'
        return destroy_response
    
    def update_instance_meta(self,req,machine_details):
        self.machine_id = machine_details.get('machine_id')
        self.gpu_type = req.get('gpu_type')
        self.num_gpus = req.get('num_gpus')
        self.hdd = req.get('hdd')
        self.is_reserved = req.get('is_reserved')
        self.name = req.get('name')
        self.num_cpus = req.get('num_cpus')
        self.url = machine_details.get('url')
        self.endpoints = machine_details.get('endpoints')
        self.ssh_str = machine_details.get('ssh_str')
        self.status = machine_details.get('status')
        self.machine_id=machine_details.get('machine_id')
        self.duration=machine_details.get('frequency')
        self.template=machine_details.get('framework')

    def resume(self,
               storage: int=None,
               num_cpus: int = None,
               num_gpus :int=None,
               gpu_type: str=None,
               name: str=None,
               script_id: str=None,
               script_args: str=None,
               is_reserved: bool=None,
               duration: str=None,
               fs_id: str=None
               ):
        resume_req = {
            'machine_id': self.machine_id,
            'hdd' :  storage or self.hdd,
            'name' : name or self.name,
            'script_id' :  script_id or self.script_id,
            'script_args' : script_args or self.script_args,
            'duration' : duration or self.duration,
            'gpu_type': None,
            'num_gpus': None,
            'num_cpus': None,
            'fs_id': fs_id
        }

        # Filter out None values so we only send user-provided arguments
        if num_cpus is not None:
            resume_req['num_cpus'] = num_cpus
        if gpu_type is not None:
            resume_req['gpu_type'] = gpu_type
        if num_gpus is not None:
            resume_req['num_gpus'] = num_gpus
        if is_reserved is not None:
            resume_req['is_reserved'] = is_reserved

        # Original logic for default GPU/CPU
        if resume_req.get('num_cpus') or (self.gpu_type == 'CPU' and not resume_req.get('num_gpus')):
            resume_req['num_cpus'] = resume_req.get('num_cpus') or self.num_cpus
        else:
            resume_req['gpu_type'] = resume_req.get('gpu_type') or self.gpu_type
            resume_req['num_gpus'] = resume_req.get('num_gpus') or self.num_gpus
            resume_req['is_reserved'] = resume_req.get('is_reserved') or self.is_reserved
        
        try:
            # Filter out keys with None values before sending
            payload = {k: v for k, v in resume_req.items() if v is not None}
            resume_resp = post(payload,f'templates/{self.template}/resume', token)
            self.machine_id = resume_resp['machine_id']
            machine_details = Instance.get_instance_details(machine_id=self.machine_id)
            self.update_instance_meta(req=resume_req,machine_details=machine_details)
            return self
        
        except InstanceCreationException:
            return {'error_message': 'Failed to create the instance. Please reach to the team.'}

        except Exception as e:
            return {'error_message' : "Some unexpected error had occured. Please reach to the team."}

    def get_instance_details(machine_id):
        attempts = 0
        max_attempts = 5

        while attempts < max_attempts:
            machine_status_response = get('users/fetch',
                                      token)
            
            matching_instances = [instance for instance in machine_status_response['instances'] 
                                if instance.get('machine_id') == machine_id]
            machine_details = matching_instances[0] if matching_instances else None
            if machine_details['status'] == 'Running':
                return machine_details
            else:
                time.sleep(10)
                attempts+= 1
        
        if attempts == max_attempts and machine_details['status'] != 'Running':
            raise InstanceCreationException

    @classmethod
    def create(cls,
               instance_type :str,
               gpu_type: str = 'RTX5000',
               template: str = 'pytorch', 
               num_gpus: int = 1,
               num_cpus: int = 1,
               storage: int = 20,
               name: str = 'Name me',
               script_id: str = None,
               image: str = None,
               script_args: str = None,
               is_reserved :bool = True,
               duration: str = 'hour',
               http_ports : str = '',
               fs_id: str = None
               ):
        req_data = {'hdd':storage,
                    'name':name,
                    'script_id':script_id,
                    'image':image,
                    'script_args':script_args,
                    'is_reserved' :is_reserved,
                    'duration':duration,
                    'http_ports' :http_ports,
                    'fs_id':fs_id}
        instance_params = {}

        if instance_type.lower() == 'gpu':
            req_data['gpu_type'] = gpu_type
            req_data['num_gpus'] = num_gpus
            instance_params['gpu_type'] = gpu_type
            instance_params['num_gpus'] = num_gpus
        elif instance_type.lower() == 'cpu':
            req_data['num_cpus'] = num_cpus
            instance_params['gpu_type'] = 'CPU'
            instance_params['num_cpus'] = num_cpus

        try:
            payload = {k: v for k, v in req_data.items() if v is not None}
            resp = post(payload, f'templates/{template}/create', token)
            machine_id = resp['machine_id']
            
            # Save the custom name
            if name and name != "My-Jarvis-Instance" and name != "Name me":
                save_instance_name(machine_id, name)
                
            machine_details = Instance.get_instance_details(machine_id=machine_id)
            instance_params.update({
                'hdd': storage,
                'name': name,  # Use the name we provided, not the one from machine_details
                'url': machine_details.get('url'),
                'endpoints': machine_details.get('endpoints'),
                'ssh_str': machine_details.get('ssh_str'),
                'status': machine_details.get('status'),
                'machine_id': machine_details.get('machine_id'),
                'duration': machine_details.get('frequency'),
                'template': machine_details.get('framework'),
        })

            instance = cls(**instance_params)
            return instance
        
        except InstanceCreationException:
            return {'error_message': 'Failed to create the instance. Please reach to the team.'}

        except Exception as e:
            return {'error_message' : "Some unexpected error had occured. Please reach to the team."}

    def __str__(self):
        """Returns a formatted string with instance metadata when the object is printed."""
        metadata = [
            f"Instance Name: {self.name}",
            f"Status: {self.status}",
            f"Machine ID: {self.machine_id}",
            f"GPU Type: {self.gpu_type}",
            f"Number of GPUs: {self.num_gpus}",
            f"Number of CPUs: {self.num_cpus}",
            f"Storage (GB): {self.hdd}",
            f"Template: {self.template}",
            f"Duration: {self.duration}",
            f"SSH Command: {self.ssh_str}",
            f"URL: {self.url}",
            f"Endpoints: {self.endpoints}"
        ]
        return "\n".join(metadata)

class InstanceCreationException(Exception):
    """Exception raised when instance creation fails."""

    def __init__(self, message="Failed to create the instance. Please check it."):
        self.message = message
        super().__init__(self.message)

class User(object):
    def __init__(self) -> None:
        pass
    
    @classmethod
    def get_instances(cls)->list[Instance]:
        resp = get(f"users/fetch", 
                    token)
        instances = []
        for instance in resp['instances']:
            machine_id = instance.get('machine_id')
            
            # First check if we have a stored custom name
            name = get_instance_name(machine_id)
            
            # If no custom name, use API name or generate one
            if not name:
                name = instance.get('name')
                if not name or name == 'N/A':
                    gpu_type = instance.get('gpu_type', 'Unknown')
                    name = f"{gpu_type} #{machine_id}"

            inst = Instance(hdd=instance.get('hdd'),
                            gpu_type=instance.get('gpu_type'),
                            machine_id=machine_id,
                            name=name,
                            is_reserved=instance.get('is_reserved'),
                            url=instance.get('url'),
                            status=instance.get('status'),
                            ssh_str=instance.get('ssh_str'),
                            num_gpus=instance.get('num_gpus'),
                            num_cpus=instance.get('num_cpus'),
                            endpoints=instance.get('endpoints'),
                            duration=instance.get('frequency'),
                            template=instance.get('framework'))
            instances.append(inst)
        return instances

    @classmethod
    def get_instance(cls, instance_id=None) -> Instance:
        instances = cls.get_instances()
        for instance in instances:
            if instance.machine_id == instance_id:
                return instance
        return None

    @classmethod
    def get_templates(cls):
        resp = get(f"templates/", 
                    token)
        return resp

    @classmethod
    def get_balance(cls):
        resp = get(f"users/credits",
                   token)
        return resp
    
    @classmethod
    def get_scripts(cls):
        resp = get(f"users/scripts",
                   token)
        return resp
    
class FileSystem(object):
    def list(self):
        return get('fs', token)

    def create(self, fs_name, storage):
        return post(dict(fs_name=fs_name,
                         storage=storage),
                    'fs',
                    token)

    def delete(self, fs_id):
        return post(dict(fs_id=fs_id),
                    'fs/delete',
                    token)