from rich.console import Console
from rich.table import Table, Column
from rich import box
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.align import Align
from rich.text import Text
import time

from .jlclient.jarvisclient import Instance

console = Console()

# Emoji indicators
STATUS_EMOJIS = {
    "Running": "🟢",
    "Paused": "🟡",
    "Stopped": "🔴",
    "Failed": "❌",
    "Creating": "⏳",
    "Destroying": "🗑️",
    "Unknown": "❓"
}

GPU_EMOJIS = {
    "RTX5000": "🎮",
    "RTX6000": "🎮",
    "V100": "🚀",
    "A100": "⚡",
    "A6000": "💪",
    "A4000": "💻",
    "RTX4090": "🎯"
}

def get_status_emoji(status):
    """Get an emoji for a given status."""
    return STATUS_EMOJIS.get(status, STATUS_EMOJIS["Unknown"])

def get_gpu_emoji(gpu_type):
    """Get an emoji for a given GPU type."""
    return GPU_EMOJIS.get(gpu_type, "🖥️")

def show_spinner(message="Processing..."):
    """Show a spinner while processing."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description=message, total=None)
        try:
            yield
        finally:
            progress.remove_task(task)

def display_instances_table(instances: list[Instance]):
    """Displays a list of instances in a rich table."""
    if not instances:
        console.print(Panel(
            Align.center("[bold yellow]No instances found yet :) Try 'jarvis create' to launch one![/]"),
            title="[bold red]JarvisLabs Instances[/]",
            border_style="red"
        ))
        return
        
    table = Table(
        Column("Name", justify="left", style="cyan", no_wrap=True),
        Column("Status", justify="center"),
        Column("ID", justify="right", style="magenta"),
        Column("GPU", justify="center", style="green"),
        Column("#GPUs", justify="right"),
        Column("Storage", justify="right"),
        Column("SSH Command", justify="left", style="yellow", no_wrap=True),
        title="[bold]🖥️ JarvisLabs Instances 🖥️[/]",
        box=box.HEAVY_EDGE,
        border_style="blue",
        header_style="bold bright_white on dark_blue",
        pad_edge=False,
        collapse_padding=True,
        min_width=80
    )

    for instance in instances:
        status = instance.status
        if status == "Running":
            style = "bold green"
        elif status == "Paused":
            style = "bold yellow"
        else:
            style = "bold red"
        
        gpu_emoji = get_gpu_emoji(instance.gpu_type)
        status_emoji = get_status_emoji(status)
        
        table.add_row(
            f"{instance.name}",
            f"[{style}]{status_emoji} {status}[/]",
            str(instance.machine_id),
            f"{gpu_emoji} {instance.gpu_type}",
            str(instance.num_gpus),
            f"{instance.hdd} GB",
            f"[bright_white on black] {instance.ssh_str} [/]"
        )
    
    console.print("\n")
    console.print(Align.center(table))
    console.print("\n")

def display_instances_for_selection(instances: list[Instance]):
    """Displays a numbered list of instances for selection."""
    if not instances:
        console.print(Panel(
            Align.center("[bold yellow]No instances available for selection :) Try 'jarvis create' first![/]"),
            title="[bold red]Select Instance[/]",
            border_style="red"
        ))
        return
        
    table = Table(
        Column("#", justify="right", style="bold yellow"),
        Column("Name", justify="left", style="cyan", no_wrap=True),
        Column("Status", justify="center"),
        Column("ID", justify="right", style="magenta"),
        Column("GPU Type", justify="center", style="green"),
        title="[bold]🔽 Select an Instance 🔽[/]",
        box=box.HEAVY_EDGE,
        border_style="bright_magenta",
        header_style="bold bright_white on dark_magenta"
    )

    for i, instance in enumerate(instances, 1):
        status = instance.status
        if status == "Running":
            style = "bold green"
        elif status == "Paused":
            style = "bold yellow"
        else:
            style = "bold red"
        
        status_emoji = get_status_emoji(status)
        gpu_emoji = get_gpu_emoji(instance.gpu_type)
        
        table.add_row(
            f"[bold bright_white on bright_black] {i} [/]",
            instance.name,
            f"[{style}]{status_emoji} {status}[/]",
            str(instance.machine_id),
            f"{gpu_emoji} {instance.gpu_type}"
        )
    
    console.print("\n")
    console.print(Align.center(table))
    console.print("\n")

def display_templates_table(templates: list):
    """Displays a list of available templates in a rich table."""
    if not templates:
        console.print(Panel(
            Align.center("[bold yellow]No templates available[/]"),
            title="[bold red]Framework Templates[/]",
            border_style="red"
        ))
        return
        
    table = Table(
        Column("ID", justify="left", style="cyan", no_wrap=True),
        Column("RAM", justify="right", style="magenta"),
        Column("CPU Cores", justify="right", style="green"),
        title="[bold]📦 Available Framework Templates 📦[/]",
        box=box.HEAVY_EDGE,
        border_style="bright_green",
        header_style="bold bright_white on dark_green"
    )

    for template in templates:
        table.add_row(
            template.get('id', 'N/A'),
            f"{template.get('ram', 'N/A')} GB",
            str(template.get('cpu_cores', 'N/A'))
        )
    
    console.print("\n")
    console.print(Align.center(table))
    console.print("\n")

def display_filesystems_table(filesystems: list):
    """Displays a list of filesystems in a rich table."""
    if not filesystems:
        console.print(Panel(
            Align.center("[bold yellow]No filesystems found[/]"),
            title="[bold red]FileSystems[/]",
            border_style="red"
        ))
        return
        
    table = Table(
        Column("ID", justify="left", style="cyan", no_wrap=True),
        Column("Name", justify="left", style="magenta", no_wrap=True),
        Column("Storage", justify="right", style="green"),
        Column("Status", justify="center"),
        title="[bold]💾 Your FileSystems 💾[/]",
        box=box.HEAVY_EDGE,
        border_style="bright_cyan",
        header_style="bold bright_white on dark_cyan"
    )

    for fs in filesystems:
        status = fs.get('status', 'Unknown')
        if status == "Ready":
            style = "bold green"
        elif status == "Creating":
            style = "bold yellow"
        else:
            style = "bold red"
            
        status_emoji = get_status_emoji(status)
        
        table.add_row(
            fs.get('id', 'N/A'),
            fs.get('fs_name', 'N/A'),
            f"{fs.get('storage', 'N/A')} GB",
            f"[{style}]{status_emoji} {status}[/]"
        )
    
    console.print("\n")
    console.print(Align.center(table))
    console.print("\n")

def display_balance(balance: float, currency: str = "USD"):
    """Displays the account balance in a visually appealing panel."""
    balance_text = Text()
    balance_text.append("Current Balance: ", style="bold bright_white")
    
    if balance > 50:
        balance_style = "bold bright_green"
    elif balance > 20:
        balance_style = "bold bright_yellow"
    else:
        balance_style = "bold bright_red"
        
    balance_text.append(f"${balance:.2f} {currency}", style=balance_style)
    
    panel = Panel(
        Align.center(balance_text),
        title="[bold]💰 Account Balance 💰[/]",
        border_style="bright_green",
        box=box.DOUBLE
    )
    
    console.print("\n")
    console.print(Align.center(panel))
    console.print("\n")

def show_operation_progress(operation: str, total_steps: int = 10):
    """Shows a progress bar for operations."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[bold green]{task.percentage:.0f}%"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(f"[cyan]{operation}...", total=total_steps)
        
        for _ in range(total_steps):
            time.sleep(0.1)  # Simulate work
            progress.update(task, advance=1) 