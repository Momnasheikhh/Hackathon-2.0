
import pandas as pd
import os

base_path = "c:/Users/hp/Downloads/archive/Training"
files = [
    "concatenated_dataset_Aug_2021_to_July_2024.csv",
    "peshawar_complete_data.csv"
]

output_file = "data_info.txt"

with open(output_file, "w") as out:
    for f in files:
        path = os.path.join(base_path, f)
        out.write(f"--- Loading {f} ---\n")
        try:
            df = pd.read_csv(path)
            out.write(f"Columns: {df.columns.tolist()}\n")
            out.write(f"Shape: {df.shape}\n")
            out.write(f"First 2 rows:\n{df.head(2).to_string()}\n")
            
            # Check for missing values
            out.write(f"Missing values:\n{df.isnull().sum().to_string()}\n")
            out.write("\n" + "="*30 + "\n")
        except Exception as e:
            out.write(f"Error reading {f}: {e}\n")
