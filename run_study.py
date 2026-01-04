import os


isotopes = ["Na22", "F18", "O15", "C11"]      # 3 Different sources
z_values = [0, 2, 4, 6, 8, 10]           # Z positions in cm
repetitions = 3                       # 3 runs per measurement
radius = [25, 50, 75, 100]            # radius in mm
# Looping over values
for iso in isotopes:
    for z in z_values:
    #for rad in radius:
        for r in range(1, repetitions + 1):
            
            print(f"--- Running: {iso} at {z}cm (Run {r}) ---")
            
            #run simulation
            cmd = f"python PET.py --iso {iso} --z_pos {z} --rep {r}"
            os.system(cmd)

print("Complete.")