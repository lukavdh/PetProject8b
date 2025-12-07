#!/usr/bin/env python3
"""
Coincidence Generator - Post-Processing
========================================

Genera coincidenze da dati Singles.

Parametro rotating:
- False: usa tutti i singles (full ring)
- True: filtra singles per simulare 2 moduli rotanti (EasyPET)
"""

import numpy as np
import argparse
import uproot


def generate_coincidences(input_file, output_file, 
                          time_window_ns=4.5,
                          min_angle_deg=100.0,
                          input_tree="Singles5",
                          rotating=False,
                          n_intervals=9):
    """
    Generate coincidences from Singles data.
    
    Parameters
    ----------
    input_file : str
        Path to input ROOT file
    output_file : str
        Path to output ROOT file
    time_window_ns : float
        Coincidence time window in nanoseconds
    min_angle_deg : float
        Minimum angular separation in degrees
    input_tree : str
        Name of input tree
    rotating : bool
        If True, filter singles to simulate rotating 2-module EasyPET
    n_intervals : int
        Number of rotation intervals (only used if rotating=True)
        
    Returns
    -------
    int
        Number of coincidences found
    """
    
    print()
    print("=" * 60)
    if rotating:
        print("  COINCIDENCE GENERATOR (EasyPET Rotating)")
    else:
        print("  COINCIDENCE GENERATOR (Full Ring)")
    print("=" * 60)
    print(f"  Input:  {input_file}")
    print(f"  Output: {output_file}")
    print(f"  Time window: {time_window_ns} ns")
    print(f"  Min angle: {min_angle_deg} deg")
    if rotating:
        print(f"  Rotating mode: {n_intervals} intervals")
    print("=" * 60)
    
    # Load Singles data
    print("\n  Loading Singles data...")
    f = uproot.open(input_file)
    tree = f[input_tree]
    
    x = tree["PostPosition_X"].array(library="np")
    y = tree["PostPosition_Y"].array(library="np")
    z = tree["PostPosition_Z"].array(library="np")
    energy = tree["TotalEnergyDeposit"].array(library="np")
    time = tree["GlobalTime"].array(library="np")
    
    n_singles = len(x)
    print(f"  Loaded {n_singles} singles")
    
    # Filter for rotating mode
    if rotating:
        from tools.filter_rotating import filter_singles_rotating, print_filter_stats
        
        print("\n  Applying rotation filter...")
        mask, stats = filter_singles_rotating(x, y, z, energy, time, rotation_speed_deg_per_sec=90.0)
        print_filter_stats(stats)
        
        # Apply filter
        x = x[mask]
        y = y[mask]
        z = z[mask]
        energy = energy[mask]
        time = time[mask]
        
        n_singles = len(x)
        print(f"\n  Singles after filter: {n_singles}")
    
    # Calculate angles
    angles = np.arctan2(y, x)
    
    # Adjust time window to data scale
    if time.max() > 1e12:
        time_window = time_window_ns * 1e3
    elif time.max() > 1e6:
        time_window = time_window_ns
    elif time.max() > 1e3:
        time_window = time_window_ns * 1e-3
    else:
        time_window = time_window_ns * 1e-9
    
    min_angle_rad = np.radians(min_angle_deg)
    
    # Sort by time
    sort_idx = np.argsort(time)
    x, y, z = x[sort_idx], y[sort_idx], z[sort_idx]
    energy, time, angles = energy[sort_idx], time[sort_idx], angles[sort_idx]
    
    # Find coincidences
    print("\n  Finding coincidences...")
    
    coinc = {
        'globalPosX1': [], 'globalPosY1': [], 'globalPosZ1': [],
        'globalPosX2': [], 'globalPosY2': [], 'globalPosZ2': [],
        'time1': [], 'time2': [], 'energy1': [], 'energy2': []
    }
    
    used = np.zeros(n_singles, dtype=bool)
    n_coinc = 0
    
    for i in range(n_singles):
        if used[i]:
            continue
        j = i + 1
        while j < n_singles and (time[j] - time[i]) < time_window:
            if not used[j]:
                angle_diff = abs(angles[i] - angles[j])
                if angle_diff > np.pi:
                    angle_diff = 2 * np.pi - angle_diff
                if angle_diff > min_angle_rad:
                    coinc['globalPosX1'].append(x[i])
                    coinc['globalPosY1'].append(y[i])
                    coinc['globalPosZ1'].append(z[i])
                    coinc['globalPosX2'].append(x[j])
                    coinc['globalPosY2'].append(y[j])
                    coinc['globalPosZ2'].append(z[j])
                    coinc['time1'].append(time[i])
                    coinc['time2'].append(time[j])
                    coinc['energy1'].append(energy[i])
                    coinc['energy2'].append(energy[j])
                    used[i] = used[j] = True
                    n_coinc += 1
                    break
            j += 1
    
    print(f"  Found {n_coinc} coincidences")
    
    if n_coinc == 0:
        print("  WARNING: No coincidences found!")
        return 0
    
    # Convert to arrays
    for key in coinc:
        coinc[key] = np.array(coinc[key])
    
    # Add metadata fields
    coinc['eventID1'] = np.arange(n_coinc)
    coinc['eventID2'] = np.arange(n_coinc)
    coinc['comptonPhantom1'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['comptonPhantom2'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['RayleighPhantom1'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['RayleighPhantom2'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['sourceID1'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['sourceID2'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['runID'] = np.zeros(n_coinc, dtype=np.int32)
    
    # Save
    print(f"\n  Saving to {output_file}...")
    with uproot.recreate(output_file) as fout:
        fout["Coincidences"] = coinc
    
    print(f"  SUCCESS: {n_coinc} coincidences saved")
    
    return n_coinc


def generate_coincidences_partial_ring(input_file, output_file, input_tree="Singles5"):
    """Generate coincidences for partial ring (2 static modules)."""
    
    print()
    print("=" * 60)
    print("  COINCIDENCE GENERATOR (Partial Ring - Static)")
    print("=" * 60)
    
    f = uproot.open(input_file)
    tree = f[input_tree]
    
    x = tree["PostPosition_X"].array(library="np")
    y = tree["PostPosition_Y"].array(library="np")
    z = tree["PostPosition_Z"].array(library="np")
    energy = tree["TotalEnergyDeposit"].array(library="np")
    time = tree["GlobalTime"].array(library="np")
    
    print(f"  Loaded {len(x)} singles")
    
    # Separate by module (x < 0 vs x > 0)
    mask1, mask2 = x < 0, x > 0
    print(f"  Module 1: {np.sum(mask1)}, Module 2: {np.sum(mask2)}")
    
    idx1 = np.where(mask1)[0]
    idx2 = np.where(mask2)[0]
    idx1 = idx1[np.argsort(time[idx1])]
    idx2 = idx2[np.argsort(time[idx2])]
    
    coinc = {
        'globalPosX1': [], 'globalPosY1': [], 'globalPosZ1': [],
        'globalPosX2': [], 'globalPosY2': [], 'globalPosZ2': [],
        'time1': [], 'time2': [], 'energy1': [], 'energy2': []
    }
    
    j = 0
    for i in idx1:
        if j >= len(idx2):
            break
        while j < len(idx2) - 1 and time[idx2[j+1]] < time[i]:
            j += 1
        k = idx2[j]
        coinc['globalPosX1'].append(x[i])
        coinc['globalPosY1'].append(y[i])
        coinc['globalPosZ1'].append(z[i])
        coinc['globalPosX2'].append(x[k])
        coinc['globalPosY2'].append(y[k])
        coinc['globalPosZ2'].append(z[k])
        coinc['time1'].append(time[i])
        coinc['time2'].append(time[k])
        coinc['energy1'].append(energy[i])
        coinc['energy2'].append(energy[k])
        j += 1
    
    n_coinc = len(coinc['time1'])
    print(f"  Created {n_coinc} coincidences")
    
    for key in coinc:
        coinc[key] = np.array(coinc[key])
    
    coinc['eventID1'] = np.arange(n_coinc)
    coinc['eventID2'] = np.arange(n_coinc)
    coinc['comptonPhantom1'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['comptonPhantom2'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['RayleighPhantom1'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['RayleighPhantom2'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['sourceID1'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['sourceID2'] = np.zeros(n_coinc, dtype=np.int32)
    coinc['runID'] = np.zeros(n_coinc, dtype=np.int32)
    
    with uproot.recreate(output_file) as fout:
        fout["Coincidences"] = coinc
    print(f"  SUCCESS: {n_coinc} coincidences saved")
    return n_coinc


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Input ROOT file")
    parser.add_argument("output", help="Output ROOT file")
    parser.add_argument("--partial-ring", action="store_true",
                        help="Use partial ring mode (2 static modules)")
    parser.add_argument("--rotating", action="store_true",
                        help="Use rotating mode (EasyPET simulation)")
    parser.add_argument("--n-intervals", type=int, default=9,
                        help="Number of rotation intervals (default: 9)")
    parser.add_argument("--time-window", type=float, default=4.5,
                        help="Time window in ns (default: 4.5)")
    parser.add_argument("--min-angle", type=float, default=100.0,
                        help="Minimum angle in degrees (default: 100)")
    args = parser.parse_args()
    
    if args.partial_ring:
        generate_coincidences_partial_ring(args.input, args.output)
    else:
        generate_coincidences(
            args.input, 
            args.output, 
            args.time_window, 
            args.min_angle,
            rotating=args.rotating,
            n_intervals=args.n_intervals
        )