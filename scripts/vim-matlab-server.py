#!/usr/bin/env python3

__author__ = "daeyun"

use_pexpect = True
if use_pexpect:
    try:
        import pexpect
    except ImportError:
        use_pexpect = False
if not use_pexpect:
    from subprocess import Popen, PIPE

import socketserver as SocketServer
import os
import random
import signal
import string
import sys
import threading
import time
from sys import stdin
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description="Vim-MATLAB Server")
parser.add_argument("cwd", help="Current working directory of the Vim buffer")
args = parser.parse_args()

# Change the current working directory
os.chdir(args.cwd)

hide_until_newline = False
auto_restart = False
server = None


class Matlab:
    def __init__(self):
        self.launch_process()

    def launch_process(self):
        self.kill()
        if use_pexpect:
            self.proc = pexpect.spawn("matlab", ["-nosplash", "-nodesktop"])
        else:
            self.proc = Popen(
                ["matlab", "-nosplash", "-nodesktop"],
                stdin=PIPE,
                close_fds=True,
                preexec_fn=os.setsid,
            )
        return self.proc

    def cancel(self):
        os.kill(self.proc.pid, signal.SIGINT)

    def kill(self):
        try:
            os.killpg(self.proc.pid, signal.SIGTERM)
        except:
            pass

    def run_code(self, code, run_timer=True):
        num_retry = 0
        rand_var = "".join(random.choice(string.ascii_uppercase) for _ in range(12))

        if run_timer:
            command = (
                "{randvar}=tic;{code},try,toc({randvar}),catch,end"
                ",clear('{randvar}');\n"
            ).format(randvar=rand_var, code=code.strip())
        else:
            command = "{}\n".format(code.strip())

        # The maximum number of characters allowed on a single line in Matlab's CLI is 4096.
        delim = "\n"
        max_line_length = 4095 - len(delim)

        # Initialize list to store command parts
        command_parts = []

        # Start iterating from the beginning of the command
        start_index = 0

        while start_index < len(command):
            # Calculate the end index for the current part
            end_index = start_index + max_line_length

            # Adjust end_index to the nearest comma within the maximum line length
            if end_index < len(command):
                while end_index > start_index and command[end_index] != ";":
                    end_index -= 1

            # Add the current part to the list of command parts
            command_parts.append(command[start_index : end_index + 1])

            # Update start_index to the next character after the current part
            start_index = end_index + 1

        # Join the command parts with the delimiter
        command_to_send = delim.join(command_parts)

        global hide_until_newline
        while num_retry < 3:
            try:
                if use_pexpect:
                    hide_until_newline = True
                    self.proc.send(command_to_send)
                else:
                    self.proc.stdin.write(command_to_send)
                    self.proc.stdin.flush()
                break
            except Exception as ex:
                print(ex)
                self.launch_process()
                num_retry += 1
                time.sleep(1)


class TCPHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        print_flush("New connection: {}".format(self.client_address))

        while True:
            msg = self.rfile.readline()
            if not msg:
                break
            msg = msg.strip().decode("utf-8")
            print_flush((msg[:74] + "...") if len(msg) > 74 else msg, end="")

            options = {
                "kill": self.server.matlab.kill,
                "cancel": self.server.matlab.cancel,
            }

            if msg in options:
                options[msg]()
            else:
                self.server.matlab.run_code(msg)
        print_flush("Connection closed: {}".format(self.client_address))


def status_monitor_thread(matlab):
    while True:
        matlab.proc.wait()
        if not auto_restart:
            break
        print_flush("Restarting...")
        matlab.launch_process()
        start_thread(target=forward_input, args=(matlab,))
        time.sleep(1)

    global server
    server.shutdown()
    server.server_close()


def output_filter(output_string):
    global hide_until_newline
    return output_string


def input_filter(input_string):
    if input_string == "\x1c":
        print_flush("Terminating")
        global auto_restart
        auto_restart = False
    return input_string


def forward_input(matlab):
    if use_pexpect:
        matlab.proc.interact(input_filter=input_filter, output_filter=output_filter)
    else:
        while True:
            matlab.proc.stdin.write(stdin.readline())


def start_thread(target=None, args=()):
    thread = threading.Thread(target=target, args=args)
    thread.daemon = True
    thread.start()


def print_flush(value, end="\n"):
    if use_pexpect:
        value += "\b" * len(value)
    sys.stdout.write(value + end)
    sys.stdout.flush()


def main():
    host, port = "localhost", 43889
    SocketServer.TCPServer.allow_reuse_address = True

    global server
    server = SocketServer.TCPServer((host, port), TCPHandler)
    server.matlab = Matlab()

    start_thread(target=forward_input, args=(server.matlab,))
    start_thread(target=status_monitor_thread, args=(server.matlab,))

    print_flush("Started server: {}".format((host, port)))
    server.serve_forever()


if __name__ == "__main__":
    main()
