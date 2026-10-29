"""Explicit physical parameters accompanying every spectrum table."""
import json


def parameters(case):
    return {
        'ne_m3': case['ne'], 'te_K': case['te'], 'ti_K': case['ti'],
        'vi_m_s': 0.0, 've_m_s': 0.0, 'B_T': case['B'],
        'nu_en_s_1': case.get('nu_e', 0.0), 'nu_ei_s_1': 0.0,
        'nu_in_s_1': case.get('nu_i', 0.0),
        'angle_k_B_deg': case['theta'], 'f_r_MHz': case['radar_hz']/1e6,
        'ion_composition_json': json.dumps(case['ions']),
        'ion_composition_fields': 'species, mass in atomic mass units, number fraction',
        'temperature_convention': 'ti_K applies to every ion species',
        'velocity_convention': 'signed component along scattering wavevector; all species stationary',
        'angle_convention': 'angle between scattering wavevector and B; 0 parallel, 90 perpendicular; ignored when B=0',
        'collision_operator': 'number-conserving neutral BGK' if case.get('nu_e',0) or case.get('nu_i',0) else 'collisionless',
        'collision_rates_convention': 'rates in s^-1, not angular frequencies or Hz; no electron-ion collisions',
    }


def attach(group, case):
    for key, value in parameters(case).items():
        group.attrs[key] = value
