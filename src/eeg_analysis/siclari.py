import logging
from copy import deepcopy
import time
import sys
import pandas as pd
import numpy as np
import mne
import mne_connectivity
from pathlib import Path
from mne.preprocessing import ICA
sys.modules["mne.connectivity"] = mne_connectivity # NOTE: monkey patching this for now. pySPI should probably fix this.
from pyspi.calculator import Calculator

# uncomment line 17 to 23 in .venv/lib/python3.11/site-packages/pyspi/statistics/infotheory.py to start jvm
# or use the following code to start jvm
# from jpype import JPackage, startJVM, getDefaultJVMPath
# startJVM(getDefaultJVMPath())

logging.basicConfig(level=logging.INFO)

def preprocess_signal(raw):
    raw.filter(l_freq=1, h_freq=50, verbose=False)
    ica = ICA(n_components=15, random_state=97, max_iter=800, verbose=False) # https://mne.tools/stable/auto_tutorials/preprocessing/40_artifact_correction_ica.html#fitting-ica
    ica.fit(raw)
    ica.apply(raw)
    return raw

def main():
    data_root = Path("/home/arashsm79/playground/eeg-analysis/data/23306054")
    records_path = data_root / "Tononi Serial Awakenings-Part1-No_PSGs/Tononi Serial Awakenings/Records.csv"
    output_path = data_root / 'measures.csv'
    pyspi_config_path = Path("src/eeg_analysis/siclari-config.yaml")

    canonical_coi_names = ['Chan 15', 'Chan 137']

    records = pd.read_csv(records_path)

    main_calc = None

    for _, row in records.iterrows():
        subject_dir = data_root / f"Tononi Serial Awakenings-Part{row['Subject ID']+1}-s{row['Subject ID']:02d}_PSGs"

        eeg_filepath = next(subject_dir.rglob(row['Filename']))
        logging.info(f"Subject ID: {row['Subject ID']}, Filename: {row['Filename']}")
        logging.info(f"Processing {eeg_filepath}")

        if row['Subject ID'] == 23:
            coi_names = [name.replace("Chan ", "") for name in canonical_coi_names] # data for subject 23 has diferent channel names
        else:
            coi_names = canonical_coi_names

        raw = mne.io.read_raw_edf(eeg_filepath, preload=True, verbose=False)

        preprocessed_data = preprocess_signal(raw)
        coi_data = preprocessed_data.get_data(picks=coi_names)

        if main_calc is None:
            main_calc = Calculator(configfile=pyspi_config_path)

        calc_set = deepcopy(main_calc)
        calc_set.name = f"{row['Subject ID']}_{row['Filename']}"
        logging.info(f"Calculating SPI between {coi_names} for {eeg_filepath}")
        coi_data = np.nan_to_num(coi_data)
        calc_set.load_dataset(coi_data)
        start_time = time.time()
        calc_set.compute()
        logging.info(f"SPI calculation took {time.time() - start_time} seconds.")
        calc_table = calc_set.table

        for feature_name in calc_table.columns.get_level_values(0).unique():
            spi = calc_table[feature_name].values[np.triu_indices_from(calc_table[feature_name], k=1)]
            row[feature_name] = spi.item()

        # save it every iteration to avoid losing data in case of crash 
        records_with_spi_df = pd.DataFrame([row])
        if not output_path.exists():
            records_with_spi_df.to_csv(output_path, index=False, header=True)
        else:
            records_with_spi_df.to_csv(output_path, mode='a', index=False, header=False)


    exit(0)

if __name__ == '__main__':
    main()