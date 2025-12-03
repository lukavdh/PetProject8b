#!/usr/bin/env python3
"""
PET Simulation Analysis Script
Analyzes OpenGATE PET simulation output and generates comprehensive report.

Usage:
    python analyze_results.py <path_to_root_file> [--stats <path_to_stats_file>]

Example:
    python analyze_results.py data/output/posvalidation/output_validate_pos2.root --stats data/output/posvalidation/stats_validate_pos2.txt
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

# Try to import uproot for ROOT file reading
try:
    import uproot
    HAS_UPROOT = True
except ImportError:
    HAS_UPROOT = False
    print("WARNING: uproot not installed. Install with: pip install uproot awkward")

def print_separator(title=""):
    """Print a separator line with optional title"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    else:
        print('-'*60)

def analyze_root_file(root_path):
    """Analyze ROOT file structure and contents"""
    
    if not HAS_UPROOT:
        print("Cannot analyze ROOT file without uproot. Please install it.")
        return None
    
    print_separator("ROOT FILE STRUCTURE")
    
    f = uproot.open(root_path)
    print(f"\nFile: {root_path}")
    print(f"Keys found: {list(f.keys())}")
    
    results = {
        'file': str(root_path),
        'trees': {}
    }
    
    for key in f.keys():
        tree_name = key.split(';')[0]  # Remove cycle number
        print_separator(f"Tree: {tree_name}")
        
        try:
            tree = f[key]
            n_entries = tree.num_entries
            branches = list(tree.keys())
            
            print(f"  Number of entries: {n_entries}")
            print(f"  Number of branches: {len(branches)}")
            print(f"  Branches: {branches[:20]}{'...' if len(branches) > 20 else ''}")
            
            results['trees'][tree_name] = {
                'entries': n_entries,
                'branches': branches
            }
            
            # If this looks like Singles data, extract statistics
            if n_entries > 0 and any('Pos' in b or 'Energy' in b or 'Time' in b for b in branches):
                print(f"\n  Sample statistics for key branches:")
                
                arrays = tree.arrays()
                
                # Energy statistics
                energy_branches = [b for b in branches if 'Energy' in b]
                for eb in energy_branches[:2]:
                    data = np.array(arrays[eb])
                    if len(data) > 0:
                        print(f"    {eb}:")
                        print(f"      Mean: {np.mean(data):.4f}")
                        print(f"      Std:  {np.std(data):.4f}")
                        print(f"      Min:  {np.min(data):.4f}")
                        print(f"      Max:  {np.max(data):.4f}")
                        results['trees'][tree_name][f'{eb}_stats'] = {
                            'mean': float(np.mean(data)),
                            'std': float(np.std(data)),
                            'min': float(np.min(data)),
                            'max': float(np.max(data))
                        }
                
                # Position statistics
                pos_branches = [b for b in branches if 'Pos' in b and ('X' in b or 'Y' in b or 'Z' in b)]
                for pb in pos_branches[:6]:
                    data = np.array(arrays[pb])
                    if len(data) > 0:
                        print(f"    {pb}:")
                        print(f"      Mean: {np.mean(data):.2f} mm")
                        print(f"      Std:  {np.std(data):.2f} mm")
                        print(f"      Range: [{np.min(data):.2f}, {np.max(data):.2f}] mm")
                        results['trees'][tree_name][f'{pb}_stats'] = {
                            'mean': float(np.mean(data)),
                            'std': float(np.std(data)),
                            'min': float(np.min(data)),
                            'max': float(np.max(data))
                        }
                
                # Time statistics
                time_branches = [b for b in branches if 'Time' in b or 'time' in b]
                for tb in time_branches[:2]:
                    data = np.array(arrays[tb])
                    if len(data) > 0:
                        print(f"    {tb}:")
                        print(f"      Mean: {np.mean(data):.6f} s")
                        print(f"      Range: [{np.min(data):.6f}, {np.max(data):.6f}] s")
                        results['trees'][tree_name][f'{tb}_stats'] = {
                            'mean': float(np.mean(data)),
                            'min': float(np.min(data)),
                            'max': float(np.max(data))
                        }
                        
        except Exception as e:
            print(f"  Error reading tree: {e}")
    
    return results, f

def generate_plots(root_path, output_dir="analysis_output"):
    """Generate all analysis plots"""
    
    if not HAS_UPROOT:
        print("Cannot generate plots without uproot.")
        return
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    f = uproot.open(root_path)
    
    print_separator("GENERATING PLOTS")
    
    # Find the main data tree (usually Singles5 or similar)
    data_tree = None
    tree_name = None
    for key in f.keys():
        if 'Singles' in key or 'Hits' in key:
            tree = f[key]
            if tree.num_entries > 0:
                data_tree = tree
                tree_name = key.split(';')[0]
                break
    
    if data_tree is None:
        print("No suitable data tree found!")
        return
    
    print(f"Using tree: {tree_name} with {data_tree.num_entries} entries")
    arrays = data_tree.arrays()
    branches = list(data_tree.keys())
    
    # 1. ENERGY SPECTRUM
    print("\n1. Generating Energy Spectrum...")
    energy_branches = [b for b in branches if 'Energy' in b and 'Deposit' in b]
    if energy_branches:
        eb = energy_branches[0]
        energy = np.array(arrays[eb]) * 1000  # Convert to keV if in MeV
        if np.max(energy) < 10:  # Likely in MeV
            energy = energy * 1000
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(energy, bins=200, range=(0, 700), histtype='step', linewidth=1.5)
        ax.axvline(511, color='r', linestyle='--', label='511 keV (annihilation)')
        ax.axvline(449.68, color='g', linestyle=':', label='Energy window (449.68-613.20 keV)')
        ax.axvline(613.20, color='g', linestyle=':')
        ax.set_xlabel('Energy (keV)')
        ax.set_ylabel('Counts')
        ax.set_title('Energy Spectrum of Detected Events')
        ax.legend()
        ax.set_xlim(0, 700)
        plt.savefig(output_dir / '01_energy_spectrum.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   Saved: {output_dir}/01_energy_spectrum.png")
    
    # 2. TRANSAXIAL POSITION (X-Y)
    print("\n2. Generating Transaxial Position Plot...")
    x_branches = [b for b in branches if 'Pos' in b and 'X' in b]
    y_branches = [b for b in branches if 'Pos' in b and 'Y' in b]
    
    if x_branches and y_branches:
        x = np.array(arrays[x_branches[0]])
        y = np.array(arrays[y_branches[0]])
        
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.scatter(x[:5000], y[:5000], s=1, alpha=0.5)  # Limit points for visibility
        ax.set_xlabel('X Position (mm)')
        ax.set_ylabel('Y Position (mm)')
        ax.set_title('Transaxial Detection Positions (X-Y plane)')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        
        # Draw approximate ring
        theta = np.linspace(0, 2*np.pi, 100)
        ring_r = 391.5  # mm, from simulation
        ax.plot(ring_r * np.cos(theta), ring_r * np.sin(theta), 'r--', alpha=0.5, label='Detector ring')
        ax.legend()
        
        plt.savefig(output_dir / '02_transaxial_position.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   Saved: {output_dir}/02_transaxial_position.png")
    
    # 3. AXIAL POSITION (Z)
    print("\n3. Generating Axial Position Histogram...")
    z_branches = [b for b in branches if 'Pos' in b and 'Z' in b]
    
    if z_branches:
        z = np.array(arrays[z_branches[0]])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(z, bins=100, histtype='step', linewidth=1.5)
        ax.set_xlabel('Z Position (mm)')
        ax.set_ylabel('Counts')
        ax.set_title('Axial Detection Position Distribution')
        ax.axvline(0, color='r', linestyle='--', alpha=0.5, label='Center (z=0)')
        ax.legend()
        
        plt.savefig(output_dir / '03_axial_position.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   Saved: {output_dir}/03_axial_position.png")
    
    # 4. TIME DISTRIBUTION
    print("\n4. Generating Time Distribution...")
    time_branches = [b for b in branches if 'Time' in b and 'Global' in b]
    
    if time_branches:
        time = np.array(arrays[time_branches[0]])
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(time, bins=100, histtype='step', linewidth=1.5)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Counts')
        ax.set_title('Temporal Distribution of Detected Events')
        
        plt.savefig(output_dir / '04_time_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   Saved: {output_dir}/04_time_distribution.png")
    
    # 5. 2D HISTOGRAM (X-Y density)
    print("\n5. Generating 2D Position Density...")
    if x_branches and y_branches:
        x = np.array(arrays[x_branches[0]])
        y = np.array(arrays[y_branches[0]])
        
        fig, ax = plt.subplots(figsize=(10, 10))
        h = ax.hist2d(x, y, bins=100, cmap='hot')
        plt.colorbar(h[3], ax=ax, label='Counts')
        ax.set_xlabel('X Position (mm)')
        ax.set_ylabel('Y Position (mm)')
        ax.set_title('2D Detection Position Density')
        ax.set_aspect('equal')
        
        plt.savefig(output_dir / '05_position_density_2d.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   Saved: {output_dir}/05_position_density_2d.png")
    
    # 6. ANGULAR DISTRIBUTION
    print("\n6. Generating Angular Distribution...")
    if x_branches and y_branches:
        x = np.array(arrays[x_branches[0]])
        y = np.array(arrays[y_branches[0]])
        
        angles = np.arctan2(y, x) * 180 / np.pi  # Convert to degrees
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(angles, bins=72, range=(-180, 180), histtype='step', linewidth=1.5)
        ax.set_xlabel('Angle (degrees)')
        ax.set_ylabel('Counts')
        ax.set_title('Angular Distribution of Detections')
        ax.set_xlim(-180, 180)
        
        plt.savefig(output_dir / '06_angular_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"   Saved: {output_dir}/06_angular_distribution.png")
    
    print(f"\nAll plots saved to: {output_dir}/")
    return output_dir

def read_stats_file(stats_path):
    """Read and parse OpenGATE statistics file"""
    
    print_separator("SIMULATION STATISTICS")
    
    stats = {}
    
    try:
        with open(stats_path, 'r') as f:
            content = f.read()
            print(content)
            
            # Parse key values
            for line in content.split('\n'):
                if ':' in line or '=' in line:
                    parts = line.replace('=', ':').split(':')
                    if len(parts) >= 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        stats[key] = value
    except Exception as e:
        print(f"Error reading stats file: {e}")
    
    return stats

def generate_summary_report(results, stats, output_dir):
    """Generate a text summary report"""
    
    report_path = Path(output_dir) / "analysis_report.txt"
    
    with open(report_path, 'w') as f:
        f.write("="*70 + "\n")
        f.write("PET SIMULATION ANALYSIS REPORT\n")
        f.write("="*70 + "\n\n")
        
        if stats:
            f.write("SIMULATION STATISTICS:\n")
            f.write("-"*40 + "\n")
            for key, value in stats.items():
                f.write(f"  {key}: {value}\n")
            f.write("\n")
        
        if results:
            f.write("ROOT FILE CONTENTS:\n")
            f.write("-"*40 + "\n")
            f.write(f"  File: {results['file']}\n\n")
            
            for tree_name, tree_data in results['trees'].items():
                f.write(f"  Tree: {tree_name}\n")
                f.write(f"    Entries: {tree_data.get('entries', 'N/A')}\n")
                f.write(f"    Branches: {len(tree_data.get('branches', []))}\n")
                
                # Write statistics for each measured quantity
                for key, value in tree_data.items():
                    if '_stats' in key:
                        branch_name = key.replace('_stats', '')
                        f.write(f"\n    {branch_name}:\n")
                        if isinstance(value, dict):
                            for stat_name, stat_value in value.items():
                                f.write(f"      {stat_name}: {stat_value}\n")
                f.write("\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("HISTOGRAM DESCRIPTIONS:\n")
        f.write("="*70 + "\n\n")
        
        histograms = [
            ("01_energy_spectrum.png", "Energy Spectrum",
             """Shows the distribution of deposited energy in the detector crystals.
             - X-axis: Energy in keV
             - Y-axis: Number of counts
             - The 511 keV photopeak corresponds to annihilation photons
             - The energy window (449.68-613.20 keV) filters valid events
             - Events below the photopeak are Compton scattered photons
             - Peak width indicates energy resolution (~11.2% FWHM)"""),
            
            ("02_transaxial_position.png", "Transaxial Detection Position",
             """Shows where photons are detected in the X-Y plane (transverse to patient axis).
             - X-axis: X position in mm
             - Y-axis: Y position in mm
             - Full ring: events form a complete circle at detector radius
             - Partial ring (2 modules): events concentrate in two arc segments
             - Source positions appear as areas of LOR intersection"""),
            
            ("03_axial_position.png", "Axial Position Distribution",
             """Shows detection positions along the scanner axis (Z direction).
             - X-axis: Z position in mm
             - Y-axis: Number of counts
             - Central peak indicates sources are centered in FOV
             - Width relates to axial extent of activity and acceptance angle
             - Should be symmetric for centered sources"""),
            
            ("04_time_distribution.png", "Temporal Distribution",
             """Shows when events are detected during the simulation.
             - X-axis: Time in seconds
             - Y-axis: Number of counts
             - Should be approximately uniform for short simulations
             - Any decay visible indicates radioactive half-life effect
             - Useful for validating simulation timing parameters"""),
            
            ("05_position_density_2d.png", "2D Detection Density",
             """Heat map showing spatial density of detections.
             - X-axis: X position in mm
             - Y-axis: Y position in mm
             - Color: Number of counts (hot = more counts)
             - Full ring: uniform ring of high density
             - Partial ring: two hot spots at active module positions
             - Useful for identifying detector uniformity issues"""),
            
            ("06_angular_distribution.png", "Angular Distribution",
             """Shows the angular distribution of detection positions.
             - X-axis: Angle in degrees (-180° to +180°)
             - Y-axis: Number of counts
             - Full ring (18 modules): relatively uniform distribution
             - Partial ring (2 modules): two peaks ~180° apart
             - Critical for understanding angular sampling completeness"""),
        ]
        
        for filename, title, description in histograms:
            f.write(f"{title} ({filename})\n")
            f.write("-"*50 + "\n")
            f.write(description + "\n\n")
    
    print(f"\nSummary report saved to: {report_path}")
    return report_path

def main():
    """Main analysis function"""
    
    print("\n" + "="*70)
    print("  PET SIMULATION ANALYSIS TOOL")
    print("="*70)
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("\nUsage: python analyze_results.py <root_file> [--stats <stats_file>]")
        print("\nExample:")
        print("  python analyze_results.py data/output/posvalidation/output_validate_pos2.root \\")
        print("         --stats data/output/posvalidation/stats_validate_pos2.txt")
        
        # Try to find files automatically
        print("\nSearching for ROOT files...")
        root_files = list(Path('.').rglob('*.root'))
        if root_files:
            print(f"Found ROOT files:")
            for rf in root_files[:5]:
                print(f"  - {rf}")
        
        stats_files = list(Path('.').rglob('stats*.txt'))
        if stats_files:
            print(f"Found stats files:")
            for sf in stats_files[:5]:
                print(f"  - {sf}")
        
        return
    
    root_path = Path(sys.argv[1])
    stats_path = None
    
    # Check for --stats argument
    if '--stats' in sys.argv:
        idx = sys.argv.index('--stats')
        if idx + 1 < len(sys.argv):
            stats_path = Path(sys.argv[idx + 1])
    
    # Validate files exist
    if not root_path.exists():
        print(f"ERROR: ROOT file not found: {root_path}")
        return
    
    # Create output directory
    output_dir = Path("analysis_output")
    output_dir.mkdir(exist_ok=True)
    
    # Analyze ROOT file
    results = None
    if HAS_UPROOT:
        results, _ = analyze_root_file(root_path)
        
        # Generate plots
        generate_plots(root_path, output_dir)
    
    # Read stats file if provided
    stats = {}
    if stats_path and stats_path.exists():
        stats = read_stats_file(stats_path)
    
    # Generate summary report
    generate_summary_report(results, stats, output_dir)
    
    print("\n" + "="*70)
    print("  ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nOutput files saved to: {output_dir}/")
    print("\nTo share results with Claude, please provide:")
    print("  1. The contents of analysis_output/analysis_report.txt")
    print("  2. The generated PNG images from analysis_output/")
    print("  3. (Optional) The stats_*.txt file contents")

if __name__ == "__main__":
    main()


