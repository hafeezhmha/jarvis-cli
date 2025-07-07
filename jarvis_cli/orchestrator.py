from rich.console import Console
from .jlclient import jarvisclient
from .jlclient.jarvisclient import User, Instance, FileSystem
from .visualisations import (
    display_instances_table, display_instances_for_selection, 
    display_templates_table, display_filesystems_table,
    show_spinner, display_balance, show_operation_progress
)

console = Console()

def set_token(token: str):
    """Sets the API token for the jarvisclient."""
    if not token:
        console.print("[bold red]Error: API token is required. Set it with --token or the JARVISLABS_TOKEN environment variable.[/]")
        raise SystemExit(1)
    jarvisclient.token = token

def list_instances():
    """Fetches and displays all user instances."""
    spinner = show_spinner("Fetching your instances...")
    next(spinner)
    try:
        instances = User.get_instances()
        if instances:
            display_instances_table(instances)
        else:
            console.print("[bold yellow]No instances found yet :) You can create one with 'jarvis create'[/]")
    except Exception as e:
        console.print(f"[bold red]Error fetching instances: {e}[/]")
        console.print("[yellow]Please ensure your API token is correct and has the necessary permissions.[/]")
    finally:
        try:
            next(spinner)
        except StopIteration:
            pass

def get_balance():
    """Fetches and displays the user's account balance."""
    spinner = show_spinner("Fetching your account balance...")
    next(spinner)
    try:
        balance_info = User.get_balance()
        if balance_info and 'balance' in balance_info:
            balance = balance_info['balance']
            display_balance(balance)
        else:
            console.print("[yellow]Could not retrieve balance information.[/]")
    except Exception as e:
        console.print(f"[bold red]Error fetching balance: {e}[/]")
    finally:
        try:
            next(spinner)
        except StopIteration:
            pass

def list_templates():
    """Fetches and displays all available framework templates."""
    spinner = show_spinner("Fetching available templates...")
    next(spinner)
    try:
        templates = User.get_templates()
        if templates:
            display_templates_table(templates)
        else:
            console.print("[yellow]No templates found.[/]")
    except Exception as e:
        console.print(f"[bold red]Error fetching templates: {e}[/]")
    finally:
        try:
            next(spinner)
        except StopIteration:
            pass

def get_instance_by_id(instance_id: int) -> Instance:
    """Retrieves a single instance by its machine ID."""
    spinner = show_spinner(f"Locating instance {instance_id}...")
    next(spinner)
    try:
        instance = User.get_instance(instance_id=instance_id)
        if not instance:
            console.print(f"[bold red]Error: Instance with ID '{instance_id}' not found.[/]")
            raise SystemExit(1)
        return instance
    finally:
        try:
            next(spinner)
        except StopIteration:
            pass

def pause_instance(instance_id: int = None):
    """Pauses a specific instance. If no ID is provided, it shows a selection list."""
    if instance_id is None:
        try:
            spinner = show_spinner("Fetching running instances...")
            next(spinner)
            try:
                instances = User.get_instances()
                running_instances = [i for i in instances if i.status == "Running"]
                if not running_instances:
                    console.print("[yellow]No running instances found to pause :) Try 'jarvis create' first![/]")
                    return
            finally:
                try:
                    next(spinner)
                except StopIteration:
                    pass

            display_instances_for_selection(running_instances)
            selection = console.input(
                "[bold cyan]Enter the number (1-" + str(len(running_instances)) + ") of the instance to pause (or 'c' to cancel): [/]"
            )

            if selection.lower() in ('c', 'cancel'):
                console.print("[bright_magenta]Pause operation cancelled.[/]")
                return

            try:
                selected_index = int(selection) - 1
                if 0 <= selected_index < len(running_instances):
                    instance_id = running_instances[selected_index].machine_id
                else:
                    console.print("[bold red]Error: Invalid selection.[/]")
                    return
            except ValueError:
                console.print("[bold red]Error: Invalid input. Please enter a number.[/]")
                return
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/]")
            return
    
    instance = get_instance_by_id(instance_id)
    if instance.status != "Running":
        console.print(f"[yellow]Instance {instance_id} is already in '{instance.status}' state.[/]")
        return
    
    console.print(f"⏸️ [bold]Pausing instance {instance_id}...[/]")
    show_operation_progress(f"Pausing instance {instance_id}")
    
    response = instance.pause()
    if response.get('success'):
        console.print(f"[bold green]✅ Successfully paused instance {instance_id}.[/]")
    else:
        console.print(f"[bold red]❌ Failed to pause instance {instance_id}: {response.get('error_message', 'Unknown error')}[/]")

def resume_instance(instance_id: int = None, gpu_type: str = None, num_gpus: int = None, num_cpus: int = None, storage: int = None, fs_id: str = None):
    """Resumes a specific instance, with optional modifications. If no ID is provided, it shows a selection list."""
    if instance_id is None:
        try:
            spinner = show_spinner("Fetching paused instances...")
            next(spinner)
            try:
                instances = User.get_instances()
                paused_instances = [i for i in instances if i.status == "Paused"]
                if not paused_instances:
                    console.print("[yellow]No paused instances found to resume :) You need to pause an instance first with 'jarvis pause'[/]")
                    return
            finally:
                try:
                    next(spinner)
                except StopIteration:
                    pass

            display_instances_for_selection(paused_instances)
            selection = console.input(
                "[bold cyan]Enter the number (1-" + str(len(paused_instances)) + ") of the instance to resume (or 'c' to cancel): [/]"
            )

            if selection.lower() in ('c', 'cancel'):
                console.print("[bright_magenta]Resume operation cancelled.[/]")
                return

            try:
                selected_index = int(selection) - 1
                if 0 <= selected_index < len(paused_instances):
                    instance_id = paused_instances[selected_index].machine_id
                else:
                    console.print("[bold red]Error: Invalid selection.[/]")
                    return
            except ValueError:
                console.print("[bold red]Error: Invalid input. Please enter a number.[/]")
                return
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/]")
            return

    instance = get_instance_by_id(instance_id)
    if instance.status != "Paused":
        console.print(f"[yellow]Instance {instance_id} is not paused. Current state: '{instance.status}'.[/]")
        return

    changes = []
    if gpu_type: changes.append(f"GPU type to {gpu_type}")
    if num_gpus: changes.append(f"GPU count to {num_gpus}")
    if num_cpus: changes.append(f"CPU count to {num_cpus}")
    if storage: changes.append(f"Storage to {storage}GB")
    if fs_id: changes.append(f"Attaching filesystem {fs_id}")
    
    change_msg = ""
    if changes:
        change_msg = f" with changes: {', '.join(changes)}"
        
    console.print(f"▶️ [bold]Resuming instance {instance_id}{change_msg}...[/]")
    show_operation_progress(f"Resuming instance {instance_id}")

    response = instance.resume(
        gpu_type=gpu_type,
        num_gpus=num_gpus,
        num_cpus=num_cpus,
        storage=storage,
        fs_id=fs_id
    )
    if isinstance(response, Instance):
        console.print(f"[bold green]✅ Successfully resumed instance {instance_id}. New status: {response.status}[/]")
    else:
        console.print(f"[bold red]❌ Failed to resume instance {instance_id}: {response.get('error_message', 'Unknown error')}[/]")


def destroy_instance(instance_id: int = None):
    """Destroys an instance. If no ID is provided, it shows a selection list."""
    if instance_id is None:
        try:
            spinner = show_spinner("Fetching instances for selection...")
            next(spinner)
            try:
                instances = User.get_instances()
                if not instances:
                    console.print("[yellow]No instances found to destroy :) Nothing to clean up![/]")
                    return
            finally:
                try:
                    next(spinner)
                except StopIteration:
                    pass

            display_instances_for_selection(instances)
            selection = console.input(
                "[bold cyan]Enter the number (1-" + str(len(instances)) + ") of a single instance to destroy (or 'c' to cancel): [/]"
            )

            if selection.lower() in ('c', 'cancel'):
                console.print("[bright_magenta]Instance destruction cancelled.[/]")
                return

            try:
                selected_index = int(selection) - 1
                if 0 <= selected_index < len(instances):
                    instance_id = instances[selected_index].machine_id
                else:
                    console.print("[bold red]Error: Invalid selection.[/]")
                    return
            except ValueError:
                console.print("[bold red]Error: Invalid input. Please enter a number.[/]")
                return
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/]")
            return

    console.print(f"[bold red]⚠️  Warning: This action is irreversible! ⚠️[/]")
    confirmation = console.input(f"[bold bright_white]Are you sure you want to destroy instance {instance_id}? (y/n): [/]")
    
    if confirmation.lower() != 'y':
        console.print("[bright_magenta]Instance destruction cancelled.[/]")
        return

    console.print(f"🗑️ [bold]Destroying instance {instance_id}...[/]")
    show_operation_progress(f"Destroying instance {instance_id}")
    
    instance = get_instance_by_id(instance_id)
    if not instance:
        return 

    response = instance.destroy()
    
    if response.get('success'):
        console.print(f"[bold green]✅ Successfully destroyed instance {instance_id}.[/]")
    else:
        console.print(f"[bold red]❌ Failed to destroy instance {instance_id}: {response.get('error_message', 'Unknown error')}[/]")

def create_instance(instance_type, name, storage, template, gpu_type, num_gpus, num_cpus, is_reserved, fs_id):
    """Creates a new instance, with an interactive prompt if needed."""
    if instance_type is None:
        console.print("[bold cyan]Choose the type of instance to create:[/]")
        console.print("  [cyan]1. GPU[/] - For machine learning, deep learning, and GPU-accelerated workloads")
        console.print("  [cyan]2. CPU[/] - For general-purpose computing and CPU-intensive workloads")
        selection = console.input("[bold bright_white]Enter your choice (1 for GPU, 2 for CPU): [/]")
        
        if selection == "1":
            instance_type = "gpu"
        elif selection == "2":
            instance_type = "cpu"
        else:
            console.print("[bold red]Error: Invalid selection. Please choose 1 (gpu) or 2 (cpu).[/]")
            return
    
    if name == "My-Jarvis-Instance":
        custom_name = console.input("[bold bright_white]Enter a custom name for your instance (or press Enter to use default): [/]")
        if custom_name.strip():
            name = custom_name

    instance_kind = "on-demand" if is_reserved else "spot"
    icon = "⚡" if instance_type == "gpu" else "💻"
    
    config_details = [
        f"Name: {name}",
        f"Type: {instance_type.upper()}",
        f"Storage: {storage}GB",
        f"Template: {template}"
    ]
    
    if instance_type == "gpu":
        config_details.append(f"GPU: {gpu_type} x {num_gpus}")
    else:
        config_details.append(f"CPUs: {num_cpus}")
        
    config_details.append(f"Mode: {instance_kind.upper()}")
    if fs_id:
        config_details.append(f"Filesystem: {fs_id}")
        
    console.print(f"\n[bold cyan]Creating new instance with configuration:[/]")
    for detail in config_details:
        console.print(f"  [bright_white]• {detail}[/]")
    
    console.print(f"\n{icon} [bold]Creating your {instance_kind} {instance_type} instance...[/]")
    show_operation_progress(f"Creating {instance_type} instance '{name}'")
    
    try:
        instance = Instance.create(
            instance_type=instance_type,
            name=name,
            storage=storage,
            template=template,
            gpu_type=gpu_type,
            num_gpus=num_gpus,
            num_cpus=num_cpus,
            is_reserved=is_reserved,
            fs_id=fs_id
        )

        if isinstance(instance, Instance):
            console.print(f"[bold green]✅ Successfully created instance with name '{name}' and ID {instance.machine_id}.[/]")
            console.print(f"[cyan]Status:[/] [bright_white]{instance.status}[/]")
            if instance.ssh_str:
                console.print("[cyan]Connect using the following SSH command:[/]")
                console.print(f"[bold black on bright_white] {instance.ssh_str} [/]")
        else:
            error_message = instance.get('error_message', 'Unknown error occurred.')
            console.print(f"[bold red]❌ Failed to create instance: {error_message}[/]")

    except Exception as e:
        console.print(f"[bold red]❌ An unexpected error occurred during instance creation: {e}[/]")

def list_filesystems():
    """Lists all filesystems."""
    spinner = show_spinner("Fetching your filesystems...")
    next(spinner)
    try:
        fs = FileSystem()
        filesystems = fs.list()
        if filesystems:
            display_filesystems_table(filesystems)
        else:
            console.print("[bold yellow]No filesystems found. Create one using 'jarvis fs create'[/]")
    except Exception as e:
        console.print(f"[bold red]Error fetching filesystems: {e}[/]")
    finally:
        try:
            next(spinner)
        except StopIteration:
            pass

def create_filesystem(name: str, storage: int):
    """Creates a new filesystem."""
    console.print(f"💾 [bold]Creating filesystem '{name}' with {storage}GB storage...[/]")
    show_operation_progress(f"Creating filesystem '{name}'")
    try:
        fs = FileSystem()
        response = fs.create(fs_name=name, storage=storage)
        if response and 'id' in response:
            console.print(f"[bold green]✅ Successfully created filesystem '{name}' with ID: {response['id']}[/]")
        else:
            console.print(f"[bold red]❌ Failed to create filesystem. Response: {response}[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error creating filesystem: {e}[/]")

def delete_filesystem(fs_id: str):
    """Deletes a filesystem."""
    console.print(f"[bold red]⚠️  Warning: This action is irreversible! ⚠️[/]")
    confirmation = console.input(f"[bold bright_white]Are you sure you want to delete filesystem {fs_id}? (y/n): [/]")
    if confirmation.lower() != 'y':
        console.print("[bright_magenta]Deletion cancelled.[/]")
        return
        
    console.print(f"🗑️ [bold]Deleting filesystem {fs_id}...[/]")
    show_operation_progress(f"Deleting filesystem {fs_id}")
    
    try:
        fs = FileSystem()
        response = fs.delete(fs_id=fs_id)
        if response and response.get('status') == 'success':
            console.print(f"[bold green]✅ Successfully deleted filesystem {fs_id}.[/]")
        else:
            console.print(f"[bold red]❌ Failed to delete filesystem {fs_id}. Response: {response}[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Error deleting filesystem: {e}[/]")

def rename_instance(instance_id: int = None, new_name: str = None):
    """Renames an instance by storing a custom name for it."""
    if instance_id is None:
        try:
            spinner = show_spinner("Fetching instances...")
            next(spinner)
            try:
                instances = User.get_instances()
                if not instances:
                    console.print("[yellow]No instances found to rename :) Create one first with 'jarvis create'[/]")
                    return
            finally:
                try:
                    next(spinner)
                except StopIteration:
                    pass

            display_instances_for_selection(instances)
            selection = console.input(
                "[bold cyan]Enter the number (1-" + str(len(instances)) + ") of the instance to rename (or 'c' to cancel): [/]"
            )

            if selection.lower() in ('c', 'cancel'):
                console.print("[bright_magenta]Rename operation cancelled.[/]")
                return

            try:
                selected_index = int(selection) - 1
                if 0 <= selected_index < len(instances):
                    instance_id = instances[selected_index].machine_id
                else:
                    console.print("[bold red]Error: Invalid selection.[/]")
                    return
            except ValueError:
                console.print("[bold red]Error: Invalid input. Please enter a number.[/]")
                return
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/]")
            return
    
    instance = get_instance_by_id(instance_id)
    if not instance:
        return
        
    if not new_name:
        current_name = instance.name
        console.print(f"[cyan]Current name:[/] {current_name}")
        new_name = console.input("[bold bright_white]Enter new name for the instance: [/]")
        
    if not new_name.strip():
        console.print("[yellow]Name cannot be empty. Rename cancelled.[/]")
        return
        
    try:
        from .jlclient.jarvisclient import save_instance_name
        save_instance_name(instance_id, new_name)
        console.print(f"[bold green]✅ Successfully renamed instance {instance_id} to '{new_name}'.[/]")
    except Exception as e:
        console.print(f"[bold red]❌ Failed to rename instance: {e}[/]") 