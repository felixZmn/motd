#!/usr/bin/env python3

# /etc/update-motd.d
# https://askubuntu.com/questions/1394600/motd-not-showing-up-on-ubuntu-21-10

import os
import platform
import psutil
from datetime import datetime
from pyfiglet import Figlet
from colorama import Fore, Style
import re

ansi_escape = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)

rabbit = f"""
      (\\(\\         /)/)
      (-.-)       (-.-)
    o_(")(")     (")(")_o
"""

# used for fstring formatting
nlspace = "\n  "


def colorize(text):
    """
    Colorize the text using ANSI escape codes.

    Args:
        text (str): Text to colorize.

    Returns:
        str: Colorized text.
    """
    return f"{Fore.GREEN}{text}{Style.RESET_ALL}"


def generate_headline(left_text, right_text, width=26):
    """
    Generates a headline with text aligned on the left and right.

    Args:
        left_text (str): Text for the left side of the headline.
        right_text (str): Text for the right side of the headline.
        width (int): Total width of the headline line.

    Returns:
        str: The formatted headline.
    """
    # Ensure the headline is properly aligned

    ll = len(ansi_escape.sub('', left_text))
    rl = len(ansi_escape.sub('', right_text))

    available_space = width - ll - rl
    return f"{left_text}{' ' * available_space}{right_text}"


def generate_progress_bar(percent, total_length=26):
    """
    Generates a progress bar with a dynamic space between the bar and the percentage.

    Args:
        percent (float): Percentage to display (0-100).
        total_length (int): Total length of the progress string (including the brackets, bar, and percentage).

    Returns:
        str: The formatted progress bar.
    """
    # Clamp percent between 0 and 100
    percent = max(0, min(100, percent))
    bar_lenght = total_length - 6

    # Calculate the filled and unfilled parts
    filled_length = round(bar_lenght * percent / 100)
    unfilled_length = bar_lenght - filled_length

    # Construct the progress bar parts
    used_part = f"{Fore.LIGHTGREEN_EX}{'=' * filled_length}{Style.RESET_ALL}"
    unused_part = f"{Fore.LIGHTBLACK_EX}{'=' * unfilled_length}{Style.RESET_ALL}"

    # Combine parts with the percentage
    bar = f"[{used_part}{unused_part}]"

    # Determine the spacing based on the percentage digits
    if percent < 10:
        space = "  "  # Two spaces for single-digit percentages
    else:
        space = " "   # One space for double-digit percentages

    percentage = f"{percent:.0f}%"

    # The total length should include both the progress bar and the percentage
    return f"{bar}{space}{percentage}".ljust(bar_lenght + 4)


def generate_header():
    # f = Figlet(font='standard')
    # return f.renderText('MALIWAN')
    return rabbit


def generate_system_info():
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    os_name = "Unknown"
    with open("/etc/os-release") as f:
        for line in f:
            if line.startswith("PRETTY_NAME="):
                os_name = line.split("=", 1)[1].strip().strip('"')
    load1, load5, load15 = os.getloadavg()

    return f"""
System info:
  Uptime...: {uptime}
  Distro...: {os_name}
  Kernel...: {platform.system()} {platform.release()}
  Load.....: {colorize(f"{load1:.2f}")} (1 min), {colorize(f"{load5:.2f}")} (5 min), {colorize(f"{load15:.2f}")} (15 min)
"""


def generate_memory_info():
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    ram_used = colorize(round(memory.used / (1024.0 ** 3)))
    ram_total = round(memory.total / (1024.0 ** 3))

    swap_used = colorize(round(swap.used / (1024.0 ** 3)))
    swap_total = round(swap.total / (1024.0 ** 3))

    mem_head = generate_headline("RAM", f"{ram_used} GiB / {ram_total} GiB")
    swap_head = generate_headline("Swap", f"{swap_used} GiB / {swap_total} GiB")
    mem_bar = generate_progress_bar(memory.percent)
    swap_bar = generate_progress_bar(swap.percent)

    return f"""
Memory:
  {mem_head}   {swap_head}
  {mem_bar}   {swap_bar}
"""


def generate_storage_info():
    disk = psutil.disk_usage('/')
    disk_used = colorize(round(disk.used / (1024.0 ** 3)))
    disk_total = round(disk.total / (1024.0 ** 3))

    disk_head = generate_headline(
        "/", f"{disk_used} GiB / {disk_total} GiB", 55)
    disk_bar = generate_progress_bar(disk.percent, 55)

    return f"""
Storage:
  {disk_head}
  {disk_bar}
"""


def generate_ingress_info():
    command = "kubectl get ingress -A -o jsonpath='{.items[*].spec.rules[*].host}'"
    ingress = set(os.popen(command).read().split())
    return f"""
Active Ingresses:
  {nlspace.join(ingress)}
    """


def generate_motd():
    motd = f"""
{generate_header()}
{generate_system_info()}
{generate_memory_info()}
{generate_storage_info()}
{generate_ingress_info()}
    """
    return motd


if __name__ == "__main__":
    print(generate_motd())
