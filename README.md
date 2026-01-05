# noirlab-query-tool

Semi-automated tool for submitting ADQL queries to [NOIRLab's Data Lab](https://datalab.noirlab.edu/). This tool handles submission of multiple queries while keeping track of what's been completed.

## Quick Start

### 1. Clone the Repository

Clone this repository to your local machine. Tip: navigate to a directory where you know you can easily find the code. E.g. I keep my codes in ~/Research/Tools/

```bash
git clone https://github.com/eriksolhaug/noirlab-query-tool.git
cd noirlab-query-tool
```

### 2. Set Up Your Environment

First, create a conda environment:

```bash
conda create -n noirlab_env python=3.11
```

When prompted "Proceed ([y]/n)?" after something like "The following NEW packages will be INSTALLED:...", please type "y" and click "Enter". The needed packages for the python environment will then be downloaded. Then run the command below to activate the newly created environment.

```bash
conda activate noirlab_env
```

NOTE: Any time you want to run this code, you will first open a terminal, then run the command above to activate the conda environment. This is a common way to avoid package version issues in the future. Once activated, you don't have to activate the environment again until you close the terminal.

Then install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Generate Queries

To create ADQL queries for a specific region:

```bash
python make_noirlab_adql.py
```

Edit the parameters in `make_noirlab_adql.py` to customize RA/Dec ranges and other settings.

### 4. Run a Query

Place `.adql` files in the `adql_queries/` directory, then run:

```bash
python submit_noirlab_adql.py
```

The script will:
- Open your browser to NOIRLab Data Lab
- Copy your ADQL query to your clipboard
- Wait for you to paste and submit the query manually
- Mark the query as done and log it when complete

You can type "q" or Ctrl+C any time to quit. The completed queries will be marked as "DONE_" in the adql_queries/ directory. When running submit_noirlab_adql.py, you will start where you left off at the next query without the prefix "DONE_".

NOTE for COOL-LAMPS: The first time you run this code, you will want to make a directory in the browser by clicking "Virtual Storage" and typing in "cool-lamps-fullsky" in the New Directory Name field. Then hit "Create" and your new directory should appear. This will be where you save the downloaded data files so you can easily identify them among previously stored files in case you've stored files in the NOIRLab browser before.

### 5. Download Results

Once your queries have been processed by NOIRLab, download the CSV results:

```bash
python download_noirlab_results.py
```

This script will:
- Prompt you to authenticate with your NOIRLab credentials
- Read `query_log.txt` to find completed queries
- Download all corresponding CSV files from NOIRLab's Virtual Object Store
- Save results to the current directory (or specify `--local_dir`)

Optional arguments:
- `--vos_dir` - Remote VOS directory (default: `cool-lamps-fullsky`)
- `--local_dir` - Local directory to save files (default: current directory)
- `--log_file` - Query log file to read (default: `query_log.txt`)

NOTE for COOL-LAMPS: Please ssh into lipwig (see below), and run the above command from inside the /usbdata/cool-lamps-fullsky/ directory. This will be where we download and store all the queried data from NOIRLab Data Lab. You do not need to specify any flags (those with "--" in front of them) as I have made the defaults right for our purpose. You will need to download the data from NOIRLab directly to lipwig (this is required since the data files can be many and quite big!) please use a conda environment on lipwig and make sure to also download the code to your home directory on lipwig. The conda executable on lipwig is located in /opt/anaconda3/bin/conda. Please follow the below workflow to download to lipwig.

```bash
conda create -n noirlab_env python=3.11
conda activate noirlab_env
cd /usbdata/cool-lamps-fullsky
python download_noirlab_results.py
```

### How to ssh into lipwig:

```bash
ssh -Y <username>@lipwig.uchicago.edu
```

## Files

- `submit_noirlab_adql.py` - Main script that handles query submission workflow
- `make_noirlab_adql.py` - Generates ADQL queries
- `download_noirlab_results.py` - Downloads completed query results from NOIRLab
- `adql_queries/` - Your ADQL query files go here
- `query_log.txt` - Auto-generated log of completed queries

## Requirements

- Firefox or other web browser
- Python 3.11+
- pyperclip (for clipboard access)
- astro-datalab (for NOIRLab authentication and file downloads)
  - Installed automatically from `requirements.txt`

## License

MIT License
