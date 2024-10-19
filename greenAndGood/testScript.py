import subprocess
import shlex

def run_ssh_command():
    # SSH command to run the energibridge on the remote server
    ssh_command = (
        'sshpass -p "greenandgood" ssh teambest@145.108.225.16 '
        '\'cd DeathStarBench/socialNetwork/ && '
        'sudo energibridge --summary -o testCristi3.csv '
        '../wrk2/wrk -D exp -t 24 -c 800 -d 60 -L '
        '-s ./wrk2/scripts/social-network/compose-post.lua '
        'http://145.108.225.16:8080/wrk2-api/post/compose -R 10\''
    )

    # Execute the SSH command
    try:
        subprocess.run(shlex.split(ssh_command), check=True)
        print("SSH command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the SSH command: {e}")

def copy_csv_file():
    # SCP command to copy the CSV file from the remote server to local desktop
    scp_command = (
        'sshpass -p "greenandgood" scp teambest@145.108.225.16:/home/teambest/DeathStarBench/socialNetwork/testCristi3.csv /Users/yyy/Projects/greenLab/experiment-runner-forked-by-me/GreenLab-experiment-runner/'
    )

    # Execute the SCP command
    try:
        subprocess.run(shlex.split(scp_command), check=True)
        print("File copied successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while copying the file: {e}")

if __name__ == "__main__":
    # Run the SSH command to execute the energibridge task
    run_ssh_command()

    # Run the SCP command to copy the CSV file
    copy_csv_file()