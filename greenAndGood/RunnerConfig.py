import itertools
import os
import random
import shlex
import signal
import subprocess
import time
from os.path import dirname, realpath
from pathlib import Path
from typing import Dict, Optional
import numpy as np
import csv

import pandas as pd
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.OperationType import OperationType
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from EventManager.EventSubscriptionController import EventSubscriptionController
from EventManager.Models.RunnerEvents import RunnerEvents
from ExtendedTyping.Typing import SupportsStr
from ProgressManager.Output.OutputProcedure import OutputProcedure as output


class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    # name:                       str             = "experiment_low"

    """The path in which Experiment Runner will create a folder with the name `self.name`, in order to store the
    results from this experiment. (Path does not need to exist - it will be created if necessary.)
    Output path defaults to the config file's path, inside the folder 'experiments'"""
    results_output_path: Path = ROOT_DIR / 'experiments'

    """Experiment operation type. Unless you manually want to initiate each run, use `OperationType.AUTO`."""
    operation_type: OperationType = OperationType.AUTO

    """The time Experiment Runner will wait after a run completes.
    This can be essential to accommodate for cooldown periods on some systems."""
    time_between_runs_in_ms: int = 1000

    # Dynamic configurations can be one-time satisfied here before the program takes the config as-is
    def __init__(self):
        """Executes immediately after program start, on config load"""
        """Initializes the RunnerConfig with graph_type and governor_type"""

        self.governor_types = ["schedutil", "performance", "powersave", "userspace", "ondemand", "conservative"]
        self.workload_types = [0, 1, 2]

        # Generate all combinations
        self.experiment_combinations = list(itertools.product(self.governor_types, self.workload_types))

        # Shuffle the combinations to randomize execution order
        random.shuffle(self.experiment_combinations)

        # Initialize index for tracking combinations
        self.combination_index = 0

        # Initialize dynamic values for each run
        self.governor_type = None
        self.workload_type = None

        self.name = f"experiment_{time.strftime('%Y%m%d_%H%M%S')}"  # Generate an experiment name based on the current time
        self.start_time = None  # Initialize start_time
        self.end_time = None  # Initialize end_time

        print(f"Experiment name: {self.name}")
        print(f"Governor type: {self.governor_type}")
        print(f"Workload type: {self.workload_type}")
        # print(f"Network type: {self.network_type}")

        EventSubscriptionController.subscribe_to_multiple_events([
            (RunnerEvents.BEFORE_EXPERIMENT, self.before_experiment),
            (RunnerEvents.BEFORE_RUN, self.before_run),
            (RunnerEvents.START_RUN, self.start_run),
            (RunnerEvents.START_MEASUREMENT, self.start_measurement),
            (RunnerEvents.INTERACT, self.interact),
            (RunnerEvents.STOP_MEASUREMENT, self.stop_measurement),
            (RunnerEvents.STOP_RUN, self.stop_run),
            (RunnerEvents.POPULATE_RUN_DATA, self.populate_run_data),
            (RunnerEvents.AFTER_EXPERIMENT, self.after_experiment)
        ])
        self.run_table_model = None  # Initialized later

        print("RunnerConfig initialized")
        output.console_log("RunnerConfig initialized")

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""

        # Extract unique values from combinations
        governor_type_values = list(set([g for g, _ in self.experiment_combinations]))
        workload_type_values = list(set([w for _, w in self.experiment_combinations]))

        # Create the factor models ensuring no duplicates
        governor_type_factor = FactorModel('governor_type', governor_type_values)
        workload_type_factor = FactorModel('workload_type', workload_type_values)

        self.run_table_model = RunTableModel(
            factors=[governor_type_factor, workload_type_factor],
            repetitions=10,
            data_columns=[
                'governor_type',
                'workload_type',
                'execution_time (seconds)',  # Execution time for the run, in seconds
                'cpu_usage',  # CPU usage percentage
                'energy',  # Energy
                'average_CPU_frequency'  # Average CPU frequency during the run
            ]
        )

        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment"""

        print("Experiment combinations:")
        for idx, (gov, workload) in enumerate(self.experiment_combinations):
            print(f"{idx}: Governor = {gov}, Workload = {workload}")


        # Ensure the next experiment combination is selected
        if self.combination_index < len(self.experiment_combinations):
            self.governor_type, self.workload_type = self.experiment_combinations[self.combination_index]
            print(f"Selected combination - Governor: {self.governor_type}, Workload: {self.workload_type}")
            # self.combination_index += 1
        else:
            print("All combinations have been executed.")

    def before_run(self) -> None:
        """Change CPU governor and initialize the social graph dynamically before starting the run."""

        """Select the next combination of governor_type, workload_type, and network_type"""
        # Delete the sar_output.txt file on the remote server if it exists
        delete_sar_command = (
            f"sshpass -p 'greenandgood' ssh teambest@145.108.225.16 'rm -f /home/teambest/sar_output.txt'"
        )
        try:
            output.console_log("Deleting sar_output.txt before starting the run")
            subprocess.check_call(shlex.split(delete_sar_command))
            output.console_log("sar_output.txt deleted successfully.")
        except subprocess.CalledProcessError as e:
            output.console_log(f"Failed to delete sar_output.txt: {e}")


        if self.combination_index < len(self.experiment_combinations):
            # Get the next combination
            self.governor_type, self.workload_type = self.experiment_combinations[self.combination_index]
            print(f"Running with Governor: {self.governor_type}, Workload: {self.workload_type}")

            # Increment the combination index for the next run
            self.combination_index += 1
        else:
            print("All experiment combinations have been executed.")

        # Change CPU governor
        governor_command = (
            f"sshpass -p 'greenandgood' ssh teambest@145.108.225.16 "
            f"'echo \"{self.governor_type}\" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'"
        )

        # Execute the governor command
        try:
            output.console_log(f"Changing CPU governor to {self.governor_type}")
            subprocess.check_call(governor_command, shell=True)
            output.console_log(f"Governor successfully changed to {self.governor_type}")

            # Adding a small sleep to ensure governor change is applied
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            output.console_log(f"Failed to change CPU governor: {e}")

        # Start monitoring CPU usage with the sar command
        sar_command = (
            'sshpass -p "greenandgood" ssh teambest@145.108.225.16 '
            '\'sar -m CPU 5 12 >> sar_output.txt\''
        )

        try:
            output.console_log("Starting CPU monitoring with 'sar'")
            subprocess.Popen(sar_command, shell=True)
            output.console_log("CPU monitoring started successfully.")
        except subprocess.CalledProcessError as e:
            output.console_log(f"Failed to start CPU monitoring: {e}")

        # Start the main task or system interaction after changing the governor
        self.target = subprocess.Popen(
            ['sshpass', '-p', '\"greenandgood\"', 'ssh', 'teambest@145.108.225.16', 'sleep 60 & echo $!'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR, shell=True
        ) # Don't think this is needed ??

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""

        """Record the start time when the run begins."""
        self.start_time = time.time()  # Record the start time
        print(f"Run started at: {self.start_time}")

        # self.target = subprocess.Popen(
        #     ['sshpass', '-p', '\"greenandgood\"', 'ssh', 'teambest@145.108.225.16', 'sleep 60 & echo $!'],
        #     stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR, shell=True
        #     )


        print(self.target)

    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""

        # Define the SSH command
        ssh_command = (
            f"sshpass -p \"greenandgood\" ssh teambest@145.108.225.16 'sudo -S powerjoular -f powerjoular_output.csv'" #TODO: check how this works 2: also use paramiko
        )

        time.sleep(1)  # allow the process to run a little before measuring
        self.profiler = subprocess.Popen(shlex.split(ssh_command))

        # Delete existing powerjoular_output.csv file on the remote server
        delete_command = (
            f"sshpass -p \"greenandgood\" ssh teambest@145.108.225.16 'rm -f powerjoular_output.csv'"
        )
        subprocess.call(shlex.split(delete_command))

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        experiments = [
            {
                "threads": 100,
                "connections": 1000,
                "observation": "± 35% LOW",
                "low": 0
            },
            {
                "threads": 100,
                "connections": 5000,
                "observation": "high variance, but a bunch of values at around 50%",
                "medium": 1
            },
            {
                "threads": 100,
                "connections": 10000,
                "observation": "± 90% HIGH",
                "high": 2
            }
        ]

        # Define the working directory and the wrk command
        wrk_command = (
            f"sshpass -p \"greenandgood\" ssh teambest@145.108.225.16 "
            f"\'cd DeathStarBench/socialNetwork/ && "
            f"../wrk2/wrk -D exp -t 100 -c {experiments[self.workload_type]['connections']} -d 60 -L "
            "-s ./wrk2/scripts/social-network/compose-post.lua "
            f"http://145.108.225.16:8080/wrk2-api/post/compose -R 2\'"

        )

        print("command workload type:", wrk_command)

        # Run the wrk2 command, changing the working directory to /home/teambest/DeathStarBench/socialNetwork
        wrk_process = subprocess.Popen(
            shlex.split(wrk_command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for the wrk2 process to complete
        output.console_log("Running wrk2 workload generation for 60 seconds")
        stdout, stderr = wrk_process.communicate()  # Block here until wrk2 finishes

        if wrk_process.returncode == 0:
            output.console_log("wrk2 command completed successfully")
            print(stdout.decode())  # Print the output of the command
        else:
            output.console_log(f"wrk2 command failed with return code {wrk_process.returncode}")
            print(stderr.decode())  # Print the error output if the command fails

        # output.console_log("Running program for 10 seconds")
        # time.sleep(10)

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""

        os.kill(self.profiler.pid, signal.SIGINT)  # graceful shutdown of powerjoular
        self.profiler.wait()

        # Wait for the powerjoular file to be written on the remote server
        time.sleep(2)  # Small delay to ensure the file is written

        # Copy the file from the remote server to the local machine using scp
        scp_command = (
            f"sshpass -p 'greenandgood' scp teambest@145.108.225.16:/home/teambest/powerjoular_output.csv {context.run_dir}"
        )

        scp_command_sar = (
            f"sshpass -p 'greenandgood' scp teambest@145.108.225.16:/home/teambest/sar_output.txt {context.run_dir}"
        )

        # Run the scp command to copy the file locally
        subprocess.check_call(shlex.split(scp_command))
        subprocess.check_call(shlex.split(scp_command_sar))

        # Delete the powerjoular_output.csv file on the remote server
        delete_command = (
            f"sshpass -p \"greenandgood\" ssh teambest@145.108.225.16 'rm -f powerjoular_output.csv'"
        )
        subprocess.call(shlex.split(delete_command))

        # Delete the sar_output.txt file on the remote server
        delete_sar_command = (
            f"sshpass -p 'greenandgood' ssh teambest@145.108.225.16 'rm -f sar_output.txt'"
        )
        subprocess.call(shlex.split(delete_sar_command))

    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""

        """Record the end time when the run finishes."""
        self.end_time = time.time()  # Record the end time
        print(f"Run ended at: {self.end_time}")

        # Calculate and log the execution time
        execution_time = self.end_time - self.start_time
        print(f"Execution time: {execution_time} seconds")

        self.target.kill()
        self.target.wait()

        # Introduce a cooldown period of 30 seconds between runs
        print("Cooldown period: waiting for 10 seconds before the next run...")
        time.sleep(5)  # Cooldown period

        print("Cooldown complete. Proceeding to the next run.")

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, SupportsStr]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        # Mapping of workload type numbers to human-readable labels
        workload_type_mapping = {
            0: 'low',
            1: 'medium',
            2: 'high'
        }

        # To account for cases where more lines than 5 are introduced by powerjoular when saving the table
        try:

            # Read the sar output file
            with open(context.run_dir / 'sar_output.txt', 'r') as file:
                lines = file.readlines()

                # Filter out unnecessary lines
            data_lines = [line.strip() for line in lines if
                          line.strip() and not line.startswith("Linux") and not line.startswith("Average")]

            # Parse the data into a list of dictionaries
            data = []
            for line in data_lines:
                parts = line.split()

                # Ensure proper parsing of time and frequency
                # Check if the line has at least 3 parts (time, 'all', frequency)
                if len(parts) >= 3 and parts[2] == 'all':
                    time = f"{parts[0]} {parts[1]}"  # Combine time and AM/PM
                    freq = parts[-1]  # Use the last part, which should be the frequency
                    try:
                        freq = int(float(freq))  # Convert to float first, then to int for proper parsing
                        data.append({"Time": time, "CPU Frequency (MHz)": freq})
                    except ValueError:
                        print(f"Warning: Could not convert frequency to int for line: {line}")
                        continue


            df_sar = pd.DataFrame(data)


            # Write the parsed data to a CSV file
            output_file = 'cpu_frequencies.csv'
            with open(output_file, 'w', newline='') as csvfile:
                fieldnames = ["Time", "CPU Frequency (MHz)"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(data)

            print(f"CSV file '{output_file}' created successfully.")


            # Load the CSV file while ignoring bad lines
            df = pd.read_csv(context.run_dir / 'powerjoular_output.csv', on_bad_lines='skip')

            # Extract the time and total power columns from the DataFrame
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Convert to datetime, handle errors
            df = df.dropna(subset=['Date'])  # Drop rows where 'Date' could not be parsed

            # Ensure 'Date' is sorted for correct time calculation
            df = df.sort_values(by='Date')
            time_seconds = (df['Date'] - df['Date'].iloc[0]).dt.total_seconds()

            total_power = pd.to_numeric(df['Total Power'], errors='coerce')
            df['CPU Utilization'] = pd.to_numeric(df['CPU Utilization'], errors='coerce')

            # Replace infinite values with NaN
            total_power.replace([np.inf, -np.inf], np.nan, inplace=True)
            df['CPU Utilization'].replace([np.inf, -np.inf], np.nan, inplace=True)

            # Fill NaN values
            total_power.fillna(0, inplace=True)
            df['CPU Utilization'].fillna(0, inplace=True)

            # Compute average CPU utilization
            average_cpu_usage = df['CPU Utilization'].mean() * 100

            # Calculate the total power consumption using the trapezoidal rule with time stamps
            total_power_consumption = np.trapz(total_power, x=time_seconds)

            # Calculate the total CPU utilization and total power consumption
            run_data = {
                'governor_type': self.governor_type,
                'workload_type': workload_type_mapping[self.workload_type],
                # Map workload type to human-readable labels
                'execution_time (seconds)': round(self.end_time - self.start_time, 3),
                'energy':  round(total_power_consumption, 3),
                'cpu_usage': round(average_cpu_usage, 2),  # Expressed as percentage
                'average_CPU_frequency': round(df_sar['CPU Frequency (MHz)'].mean(), 3)
            }

            return run_data

        except pd.errors.ParserError as e:
            output.console_log(f"CSV parsing failed: {e}")
            return None

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here.
        Invoked only once during the lifetime of the program."""

        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path: Path = None
