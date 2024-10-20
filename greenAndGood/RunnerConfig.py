import shlex
import subprocess
import time

from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ExtendedTyping.Typing import SupportsStr
from ProgressManager.Output.OutputProcedure import OutputProcedure as output

from typing import Dict, Optional
from pathlib import Path
from os.path import dirname, realpath
import os
import signal
import pandas as pd


class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    name:                       str             = "new_runner_experiment11"

    """The path in which Experiment Runner will create a folder with the name `self.name`, in order to store the
    results from this experiment. (Path does not need to exist - it will be created if necessary.)
    Output path defaults to the config file's path, inside the folder 'experiments'"""
    results_output_path:        Path            = ROOT_DIR / 'experiments'

    """Experiment operation type. Unless you manually want to initiate each run, use `OperationType.AUTO`."""
    operation_type:             OperationType   = OperationType.AUTO

    """The time Experiment Runner will wait after a run completes.
    This can be essential to accommodate for cooldown periods on some systems."""
    time_between_runs_in_ms:    int             = 1000

    # Dynamic configurations can be one-time satisfied here before the program takes the config as-is
    # e.g. Setting some variable based on some criteria
    def __init__(self):
        """Executes immediately after program start, on config load"""

        EventSubscriptionController.subscribe_to_multiple_events([
            (RunnerEvents.BEFORE_EXPERIMENT, self.before_experiment),
            (RunnerEvents.BEFORE_RUN       , self.before_run       ),
            (RunnerEvents.START_RUN        , self.start_run        ),
            (RunnerEvents.START_MEASUREMENT, self.start_measurement),
            (RunnerEvents.INTERACT         , self.interact         ),
            (RunnerEvents.STOP_MEASUREMENT , self.stop_measurement ),
            (RunnerEvents.STOP_RUN         , self.stop_run         ),
            (RunnerEvents.POPULATE_RUN_DATA, self.populate_run_data),
            (RunnerEvents.AFTER_EXPERIMENT , self.after_experiment )
        ])
        self.run_table_model = None  # Initialized later

        output.console_log("RunnerConfig initialized")

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""
        # Define any factors influencing the experiment (e.g., sampling frequency or any other dynamic configuration)
        sampling_factor = FactorModel("sampling", [10, 50, 100])

        # Define the data columns that are part of the table
        self.run_table_model = RunTableModel(
            factors=[sampling_factor],
            # data_columns=[
            #     'run_id',                # Unique identifier for each run
            #     'status',                # Status of the run (success, failure, etc.)
            #     'run_number',            # Sequential number for the run
            #     'execution_time',        # Total execution time in seconds
            #     'cpu_usage',             # CPU usage percentage
            #     'memory_usage',          # Memory usage in MB or percentage
            #     'energy_usage',          # Total energy consumption (e.g., in joules)
            #     'average_CPU_frequency', # Average CPU frequency during the run
            #     'workload_type',         # Type of workload (e.g., CPU-bound, IO-bound)
            #     'governor'               # CPU governor (e.g., performance, powersave)
            # ]
            data_columns=[
                    'cpu_usage',             # CPU usage percentage
                    'total_power'           # Total Power
                    # 'workload_type'          # What type of workload is the network under
                ]
        )

        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment here
        Invoked only once during the lifetime of the program."""

        pass

    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""

        # Change CPU governor
        governor_command = (
            "sshpass -p 'greenandgood' ssh teambest@145.108.225.16 "
            "'echo \"ondemand\" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'"
        )

        # Run the command using subprocess
        try:
            output.console_log("Changing CPU governor to schedutil")
            subprocess.check_call(governor_command, shell=True)
            output.console_log("Governor successfully changed to schedutil")

            # Adding a small sleep to ensure governor change is applied
            time.sleep(2)
        except subprocess.CalledProcessError as e:
            output.console_log(f"Failed to change CPU governor: {e}")

        # Start the main task or system interaction after changing the governor
        self.target = subprocess.Popen(
            ['sshpass', '-p', '\"greenandgood\"', 'ssh', 'teambest@145.108.225.16', 'sleep 60 & echo $!'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR, shell=True
        )

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure.
        Activities after starting the run should also be performed here."""

        self.target = subprocess.Popen(['sshpass', '-p', '\"greenandgood\"', 'ssh', 'teambest@145.108.225.16', 'sleep 60 & echo $!'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self.ROOT_DIR, shell=True
        )

        # self.target = self.target.stdout.read()
        print(self.target)


    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""

        # Define the SSH command
        ssh_command = (
            f"sshpass -p \"greenandgood\" ssh teambest@145.108.225.16 'sudo -S powerjoular -f powerjoular_remote2.csv'"
        )

        time.sleep(1) # allow the process to run a little before measuring
        self.profiler = subprocess.Popen(shlex.split(ssh_command))


    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        # Define the working directory and the wrk command
        wrk_command = (
            "sshpass -p \"greenandgood\" ssh teambest@145.108.225.16 "
            "\'cd DeathStarBench/socialNetwork/ && "
            "../wrk2/wrk -D exp -t 24 -c 800 -d 60 -L "
            "-s ./wrk2/scripts/social-network/compose-post.lua "
            "http://145.108.225.16:8080/wrk2-api/post/compose -R 10\'"
        )

        # Run the wrk2 command, changing the working directory to /home/teambest/DeathStarBench/socialNetwork
        wrk_process = subprocess.Popen(
            shlex.split(wrk_command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # cwd=working_dir  # This sets the working directory for the wrk command
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

        output.console_log("Running program for 65 seconds")
        time.sleep(65)

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""

        os.kill(self.profiler.pid, signal.SIGINT) # graceful shutdown of powerjoular
        self.profiler.wait()

        # Wait for the powerjoular file to be written on the remote server
        time.sleep(2)  # Small delay to ensure the file is written

        # Copy the file from the remote server to the local machine using scp
        scp_command = (
            f"sshpass -p 'greenandgood' scp teambest@145.108.225.16:/home/teambest/powerjoular_remote2.csv {context.run_dir}"
        )

        print("scp_command: " + scp_command)

        # Run the scp command to copy the file locally
        subprocess.check_call(shlex.split(scp_command))

    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""

        self.target.kill()
        self.target.wait()

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, SupportsStr]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        #To account for cases where more lines than 5 are introduced by powerjoular when saving the table
        try:
            # Load the CSV file while ignoring bad lines
            df = pd.read_csv(context.run_dir / 'powerjoular_remote2.csv', on_bad_lines='skip')

            # Calculate the total CPU utilization and total power consumption
            run_data = {
                'cpu_usage': round(df['CPU Utilization'].mean(), 3),
                'total_power': round(df['Total Power'].sum(), 3)
            }

            return run_data

        except pd.errors.ParserError as e:
            output.console_log(f"CSV parsing failed: {e}")
            return None

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""
        pass

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None