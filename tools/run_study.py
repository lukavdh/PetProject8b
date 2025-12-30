import os

# --- Configuration ---
isotopes = ["Na22""F18", "O15", "C11"]      # 3 Different sources (No Na22)
z_values = [0, 2, 4, 6, 8, 10]           # Z positions in cm
repetitions = 3                       # 3 runs per measurement

# --- The Loops ---
for iso in isotopes:
    for z in z_values:
        for r in range(1, repetitions + 1):
            
            print(f"--- Running: {iso} at {z}cm (Run {r}) ---")
            
            # 1. Run Simulation
            # This calls your modified PET.py with the specific settings
            cmd = f"python PET.py --iso {iso} --z_pos {z} --rep {r}"
            os.system(cmd)
            
            # 2. (Optional) Run Coincidences immediately after
            # Note: You'll need to match the filename structure defined in PET.py
            # name = f"{iso}_Z{z}cm_run{r}"
            # os.system(f"python generate_coincidences.py data/output/posvalidation/output_{name}.root data/output/posvalidation/{name}_coinc.root")

print("All simulations complete.")