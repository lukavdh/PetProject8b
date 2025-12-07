#!/usr/bin/env python3
"""
Filter Rotating Module - Filtra singles per simulare 2 moduli rotanti (EasyPET)
Velocità di rotazione costante, indipendente dalla durata simulazione.
"""

import numpy as np


def get_module_id(x, y, n_modules=18):
    """Calcola ID modulo dalla posizione."""
    angle = np.arctan2(y, x) + np.pi
    module_id = (angle / (2 * np.pi) * n_modules).astype(int)
    module_id = module_id % n_modules
    return module_id


def filter_singles_rotating(x, y, z, energy, time, 
                            rotation_speed_deg_per_sec=90.0,
                            n_modules=18):
    """
    Filtra singles per simulare 2 moduli rotanti.
    
    Parameters
    ----------
    rotation_speed_deg_per_sec : float
        Velocità di rotazione in gradi/secondo.
        90 deg/s = 1 rotazione completa (180°) ogni 2 secondi.
        180 deg/s = 1 rotazione completa ogni secondo.
    """
    n_singles = len(x)
    
    # Calcola modulo per ogni single
    module_id = get_module_id(x, y, n_modules)
    
    # Tempo in secondi (converti se necessario)
    time_min = time.min()
    time_sec = time - time_min
    
    # Converti a secondi se in ps o ns
    if time.max() > 1e12:
        time_sec = time_sec / 1e12  # ps to s
    elif time.max() > 1e9:
        time_sec = time_sec / 1e9   # ns to s
    
    # Angolo di rotazione al tempo t
    # angle(t) = rotation_speed * t
    rotation_angle = rotation_speed_deg_per_sec * time_sec
    
    # Modulo attivo al tempo t (cicla ogni 180° perché ci sono 2 moduli opposti)
    # Ogni modulo copre 20° (360°/18), quindi 180°/20° = 9 moduli per semi-rotazione
    degrees_per_module = 360.0 / n_modules  # 20° per 18 moduli
    
    # Quale coppia di moduli è attiva
    active_module_a = (rotation_angle / degrees_per_module).astype(int) % (n_modules // 2)
    active_module_b = active_module_a + (n_modules // 2)
    
    # Filtra: mantieni solo singles da moduli attivi al loro tempo
    mask = (module_id == active_module_a) | (module_id == active_module_b)
    
    # Calcola numero effettivo di intervalli
    total_time_sec = time_sec.max() - time_sec.min()
    total_rotation_deg = rotation_speed_deg_per_sec * total_time_sec
    n_intervals = int(total_rotation_deg / degrees_per_module)
    #!/usr/bin/env python3
"""
Filter Rotating Module - Filtra singles per simulare 2 moduli rotanti (EasyPET)
"""

import numpy as np


def get_module_id(x, y, n_modules=18):
    """Calcola ID modulo dalla posizione."""
    angle = np.arctan2(y, x) + np.pi
    module_id = (angle / (2 * np.pi) * n_modules).astype(int)
    module_id = module_id % n_modules
    return module_id


def filter_singles_rotating(x, y, z, energy, time, 
                            rotation_speed_deg_per_sec=90.0,
                            n_modules=18):
    """Filtra singles per simulare 2 moduli rotanti."""
    n_singles = len(x)
    
    module_id = get_module_id(x, y, n_modules)
    
    time_min = time.min()
    time_sec = time - time_min
    
    if time.max() > 1e12:
        time_sec = time_sec / 1e12
    elif time.max() > 1e9:
        time_sec = time_sec / 1e9
    
    rotation_angle = rotation_speed_deg_per_sec * time_sec
    degrees_per_module = 360.0 / n_modules
    
    active_module_a = (rotation_angle / degrees_per_module).astype(int) % (n_modules // 2)
    active_module_b = active_module_a + (n_modules // 2)
    
    mask = (module_id == active_module_a) | (module_id == active_module_b)
    
    total_time_sec = time_sec.max() - time_sec.min()
    
    stats = {
        'n_total': n_singles,
        'n_filtered': mask.sum(),
        'percentage': 100 * mask.sum() / n_singles if n_singles > 0 else 0,
        'rotation_speed': rotation_speed_deg_per_sec,
        'total_time_sec': total_time_sec
    }
    
    return mask, stats


def print_filter_stats(stats):
    """Stampa solo statistiche reali."""
    print(f"\n  Filter Results:")
    print(f"    Singles loaded:   {stats['n_total']}")
    print(f"    Singles filtered: {stats['n_filtered']} ({stats['percentage']:.1f}%)")
    print(f"    Rotation speed:   {stats['rotation_speed']} deg/s")
    print(f"    Simulation time:  {stats['total_time_sec']:.2f} s")