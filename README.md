# Experiment-Runner

More details about the Experiment-Runner initiative and it's source code can be found [here](https://github.com/S2-group/experiment-runner)

## Requirements
The experiments have been run on a Macbook, with MacOS version 15.1.1. Python3, version 3.13 has been used throughout the experiment. The terminal commands presented in this section are working on a MacOS system.

To get started:

```bash
git clone https://github.com/dalviebenu/GreenLab.git
cd GreenLab/
```
For the next step, of installing the requirements, a virtual environment needs to be created:

```bash
python3 -m venv venv
```
To activate the virtual environment on Macbook:

- Macbook:
```bash
source venv/bin/activate
```

After creating the virtual environment, run:

```bash
pip install -r requirements.txt
```

## Running the project

In this section, we assume as the current working directory, the root directory of the project.

To start the run of the experiment, this command should be used (tested on Macbook):

```bash
python3 experiment-runner/ greenAndGood/RunnerConfig.py
```

The results of the experiment will be stored in the [greenAndGood/experiments](`greenAndGood/experiments`) directory.

### Data Analysis
For performing statistical tests on the data generated from the experiment follow the instructions provided in [Data Analysis](data-analysis/README.md)

