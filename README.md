# DNMR

This repository contains a modified version of **DNMR** with additional tools for **T2 analysis**, **T1 fitting**, **data visualization** and exporting of data together with analysis settings.

The original **DNMR** software was developed by **Davis Garrad**.  
Original repository: https://github.com/Davis-Garrad/DNMR

The repository was extended by **Giacomo Panzera** later.
His repository: https://github.com/Jack-er-programmatore/DNMR-T2


## Note

This repository contains the **full modified DNMR source code**.  
It is **not necessary** to download the original DNMR repository separately.

## Added Features

### T2 Fit Tab

The **T2 Fit** tab:

- integrates the selected frequency-domain region;
- plots the integrated signal as a function of echo time;
- fits the decay to extract **T2**.

The fitting model is:

```text
S(t) = A * exp(-(t / T2)^r) + c
```

### T1 Fit Tab

The **T1 Fit** tab includes multiple fitting models for the analysis of T1 relaxation experiments.

### Plotting Tab

The **Plotting** tab allows visualization of acquired experimental variables, including environmental ones. This tab provides a convenient way to inspect experimental conditions and monitor parameter evolution throughout measurements.

### Exporting Data

This feature existed before, but was strongly modified. The export will now give a csv file containing the fitted data, results and settings used for the fit. This is intended to make any analysis reproducible later.

## Installation

Python packages can sometimes conflict with each other, especially when different projects require different package versions.

For this reason, it is recommended to install **DNMR-T2** inside a dedicated **virtual environment**.  
This is **not mandatory**, but it helps avoid unwanted installation and compatibility errors.

The recommended Python version is **Python 3.12**.  
Higher Python versions may not work correctly with all required dependencies.

Open **PowerShell** and move to the main project folder, i.e. the folder containing `pyproject.toml`, `README.md`, and `src`:

```powershell
cd C:\Users\your_username\path_to\DNMR-T2
```

Create and activate a virtual environment:

```powershell
py -3.12 -m venv dnmr-env312
.\dnmr-env312\Scripts\Activate.ps1
```

When the virtual environment is active, the PowerShell prompt should start with:

```text
(dnmr-env312)
```

Install the required packages and install **DNMR-T2** from this repository:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install "numpy==1.26.4"
python -m pip install .
python -m pip install scipy
```

The command below installs **DNMR-T2** from the current repository folder:

```powershell
python -m pip install .
```

## pytnt Patch

In some cases, `pytnt` may raise an error related to `numpy.dual`.

If this happens, run the following command once, while the virtual environment is active:

```powershell
python -c "from pathlib import Path; import sysconfig; p=Path(sysconfig.get_paths()['purelib'])/'pytnt'/'processTNT.py'; s=p.read_text(); s=s.replace('import numpy.dual as npfast', 'import numpy.linalg as npfast'); p.write_text(s); print('Patch pytnt done:', p)"
```

## Run DNMR

With the virtual environment active, run:

```powershell
python -m DNMR
```