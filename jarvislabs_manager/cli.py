import argparse
import os
import sys
from collections import OrderedDict

from rich.console import Console
from rich.table import Table

from . import orchestrator

console = Console()
__version__ = "1.0.0"

def welcome_banner() -> None:
    """Displays a welcome banner for the tool."""
    banner = rf"""
[bold bright_blue]
      ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗     ██████╗██╗     ██╗
      ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    ██╔════╝██║     ██║
      ██║███████║██████╔╝██║   ██║██║███████╗    ██║     ██║     ██║
 ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║    ██║     ██║     ██║
 ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║    ╚██████╗███████╗██║
  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝     ╚═════╝╚══════╝╚═╝
                 JARVIS CLI (v{__version__})
[/]
"""
    console.print(banner)

def exit_message() -> None:
    """Displays an exit message."""
    console.print("[bold green]Exiting Jarvis CLI. Goodbye![/]")

def display_commands() -> None:
    """Displays all available commands with their descriptions."""
    table = Table(title="Jarvis CLI Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    
    commands = OrderedDict([
        ("start", "Start Jarvis CLI with welcome banner"),
        ("exit", "Exit Jarvis CLI with goodbye message"),
        ("list", "List all your instances"),
        ("balance", "Check your account balance"),
        ("templates", "List available framework templates"),
        ("fs list", "List all filesystems"),
        ("fs create <name> <storage>", "Create a new filesystem with name and storage size in GB"),
        ("fs delete <fs_id>", "Delete a filesystem with the specified ID"),
        ("pause <instance_id>", "Pause a running instance"),
        ("resume <instance_id>", "Resume a paused instance"),
        ("destroy [instance_id]", "Destroy an instance (optional instance_id)"),
        ("create", "Create a new instance with options"),
        ("cmd", "Show this command list"),
        ("rename", "Rename an instance")
    ])
    
    for cmd, desc in commands.items():
        table.add_row(f"jarvis {cmd}", desc)
    
    console.print(table)
    
    # Display advanced create options
    create_table = Table(title="Advanced Instance Creation Options")
    create_table.add_column("Option", style="cyan")
    create_table.add_column("Description", style="green")
    create_table.add_column("Default", style="yellow")
    
    create_options = [
        ("--instance-type", "Type of instance (gpu or cpu)", "None (interactive)"),
        ("--gpu-type", "GPU type (RTX5000, A100, V100, etc.)", "RTX5000"),
        ("--num-gpus", "Number of GPUs", "1"),
        ("--num-cpus", "Number of CPUs", "1"),
        ("--storage", "Storage size in GB", "20"),
        ("--name", "Name for the instance", "My-Jarvis-Instance"),
        ("--template", "Framework template", "pytorch"),
        ("--spot", "Request spot instance (cheaper but can be terminated)", "False"),
        ("--fs-id", "Attach a filesystem by ID", "None")
    ]
    
    for option, desc, default in create_options:
        create_table.add_row(option, desc, default)
    
    console.print("\n[bold]Example GPU instance creation commands:[/]")
    console.print("  [cyan]jarvis create --instance-type gpu --gpu-type RTX5000[/] - Create RTX5000 instance (24GB VRAM)")
    console.print("  [cyan]jarvis create --instance-type gpu --gpu-type A100 --num-gpus 2[/] - Create dual A100 instance (2x80GB VRAM)")
    console.print("  [cyan]jarvis create --instance-type gpu --gpu-type V100 --spot[/] - Create V100 spot instance (16GB VRAM)")
    console.print("\nFor detailed options:")
    console.print(create_table)

def main() -> int:
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(description="A CLI tool to manage Jarvislabs.ai instances.")
    parser.add_argument(
        "--token",
        help="Your Jarvislabs API token. Can also be set via JARVISLABS_TOKEN environment variable.",
        default=os.environ.get("JARVISLABS_TOKEN"),
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Start command
    subparsers.add_parser("start", help="Start Jarvis CLI with welcome banner.")
    
    # Exit command
    subparsers.add_parser("exit", help="Exit Jarvis CLI with goodbye message.")

    # List command
    subparsers.add_parser("list", help="List all your instances.")

    # Balance command
    subparsers.add_parser("balance", help="Check your account balance.")

    # Templates command
    subparsers.add_parser("templates", help="List available framework templates.")

    # Commands list
    subparsers.add_parser("cmd", help="Show all available commands with descriptions.")

    # Filesystem command group
    fs_parser = subparsers.add_parser("fs", help="Manage filesystems.").add_subparsers(dest="fs_command", required=True)
    fs_parser.add_parser("list", help="List all filesystems.")
    create_fs_parser = fs_parser.add_parser("create", help="Create a new filesystem.")
    create_fs_parser.add_argument("name", type=str, help="Name for the new filesystem.")
    create_fs_parser.add_argument("storage", type=int, help="Storage size in GB.")
    delete_fs_parser = fs_parser.add_parser("delete", help="Delete a filesystem.")
    delete_fs_parser.add_argument("fs_id", type=str, help="The ID of the filesystem to delete.")

    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause a running instance.")
    pause_parser.add_argument("instance_id", type=int, nargs="?", default=None, help="The machine ID of the instance to pause (optional).")

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a paused instance.")
    resume_parser.add_argument("instance_id", type=int, nargs="?", default=None, help="The machine ID of the instance to resume (optional).")
    resume_parser.add_argument("--gpu-type", type=str, help="New GPU type to switch to.")
    resume_parser.add_argument("--num-gpus", type=int, help="New number of GPUs.")
    resume_parser.add_argument("--num-cpus", type=int, help="New number of CPUs.")
    resume_parser.add_argument("--storage", type=int, help="New storage size in GB.")
    resume_parser.add_argument("--fs-id", type=str, help="Filesystem ID to attach.")

    # Destroy command
    destroy_parser = subparsers.add_parser("destroy", help="Destroy an instance.")
    destroy_parser.add_argument("instance_id", type=int, nargs="?", default=None, help="The machine ID of the instance to destroy (optional).")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new instance.")
    create_parser.add_argument("--instance-type", type=str, nargs="?", default=None, choices=['gpu', 'cpu'], help="Type of instance to create (gpu or cpu).")
    create_parser.add_argument("--name", type=str, default="My-Jarvis-Instance", help="Name for the new instance.")
    create_parser.add_argument("--storage", type=int, default=20, help="Storage size in GB.")
    create_parser.add_argument("--template", type=str, default="pytorch", help="Framework template to use.")
    create_parser.add_argument("--gpu-type", type=str, default="RTX5000", help="GPU type (if instance-type is gpu).")
    create_parser.add_argument("--num-gpus", type=int, default=1, help="Number of GPUs (if instance-type is gpu).")
    create_parser.add_argument("--num-cpus", type=int, default=1, help="Number of CPUs (if instance-type is cpu).")
    create_parser.add_argument("--spot", action="store_true", help="Request a spot instance instead of on-demand.")
    create_parser.add_argument("--fs-id", type=str, help="Filesystem ID to attach.")

    # Rename command
    rename_parser = subparsers.add_parser("rename", help="Rename an instance.")
    rename_parser.add_argument("instance_id", type=int, nargs="?", default=None, help="The machine ID of the instance to rename (optional).")
    rename_parser.add_argument("name", type=str, nargs="?", default=None, help="The new name for the instance. If not provided, you'll be prompted.")

    args = parser.parse_args()

    # Set the token for the client to use
    orchestrator.set_token(args.token)

    # Only show the banner for the start command
    if args.command == "start":
        welcome_banner()
        console.print("[bold green]Jarvis CLI started successfully![/]")
        return 0
        
    # Exit command
    if args.command == "exit":
        exit_message()
        return 0

    # Execute the command
    if args.command == "list":
        orchestrator.list_instances()
    elif args.command == "balance":
        orchestrator.get_balance()
    elif args.command == "templates":
        orchestrator.list_templates()
    elif args.command == "cmd":
        display_commands()
    elif args.command == "fs":
        if args.fs_command == "list":
            orchestrator.list_filesystems()
        elif args.fs_command == "create":
            orchestrator.create_filesystem(args.name, args.storage)
        elif args.fs_command == "delete":
            orchestrator.delete_filesystem(args.fs_id)
    elif args.command == "pause":
        orchestrator.pause_instance(args.instance_id)
    elif args.command == "resume":
        orchestrator.resume_instance(
            args.instance_id,
            gpu_type=args.gpu_type,
            num_gpus=args.num_gpus,
            num_cpus=args.num_cpus,
            storage=args.storage,
            fs_id=args.fs_id
        )
    elif args.command == "destroy":
        orchestrator.destroy_instance(args.instance_id)
    elif args.command == "create":
        orchestrator.create_instance(
            instance_type=args.instance_type,
            name=args.name,
            storage=args.storage,
            template=args.template,
            gpu_type=args.gpu_type,
            num_gpus=args.num_gpus,
            num_cpus=args.num_cpus,
            is_reserved=not args.spot,
            fs_id=args.fs_id
        )
    elif args.command == "rename":
        orchestrator.rename_instance(args.instance_id, args.name)

    return 0

if __name__ == "__main__":
    sys.exit(main()) 