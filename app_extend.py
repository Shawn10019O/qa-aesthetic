"""
run_ikebana_extend_optimization:
  Extend an existing ikebana arrangement by optimizing two additional branches
  using QUBO via OpenJij.
"""

import openjij as oj
import random


def run_ikebana_extend_optimization(
    base_assignments: dict,
    base_lengths: dict,
    base_angles: dict
) -> dict:

    """
    Args:
        base_assignments: dict of selected flowers for main/guest/middle1/middle2
        base_lengths: dict of their lengths
        base_angles: dict of their azimuth/elevation angles

    Returns:
        dict with assignments, lengths, and angles for middle3 & middle4
    """
    candidate_lengths = {
        '紅梅': [40, 35, 30],
        '啓扇桜':   [40, 35, 20],
        "リアトリス": [40, 35, 30],
        # "ディル": [40, 35, 20],
    }

    max_length = base_lengths['main']

    # Build domain (flower, idx, length)
    domain = []
    for flower, lengths in candidate_lengths.items():
        for idx, length in enumerate(lengths):
            domain.append((flower, idx, length))
    n_dom = len(domain)

    az_cands = [-70,-60,-50,50,60,70]
    el_cands = [15, 20, 21]
    n_az = len(az_cands)
    n_el = len(el_cands)

    off = 0
    off3_az = off; off += n_az
    off3_el = off; off += n_el
    off3_dom = off; off += n_dom
    off4_az = off; off += n_az
    off4_el = off; off += n_el
    off4_dom = off; off += n_dom

    # Construct QUBO matrix Q
    Q = {}

    def add_q(i, j, v):
        if i > j:
            i, j = j, i
        Q[(i, j)] = Q.get((i, j), 0.0) + v

    # One-hot constraint: ensure exactly one selection per variable group
    def one_hot(offset, count, A=300.0):
        for i in range(count):
            idx = offset + i
            add_q(idx, idx, A)   
            add_q(idx, idx, -2*A) 
            for j in range(i+1, count):
                add_q(idx, offset+j, 2*A)

    one_hot(off3_az, n_az)
    one_hot(off3_el, n_el)
    one_hot(off3_dom, n_dom)
    one_hot(off4_az, n_az)
    one_hot(off4_el, n_el)
    one_hot(off4_dom, n_dom)

    # Penalty to prevent lengths from exceeding the main branch length
    lambda_len = 10.0
    for i, (_, _, length) in enumerate(domain):
        if length > max_length:
            cost = (length - max_length)**2
            add_q(off3_dom + i, off3_dom + i, cost * lambda_len)
            add_q(off4_dom + i, off4_dom + i, cost * lambda_len)

    # Angle deviation penalty: discourage new branches too close to existing ones 
    lambda_ang = 1.0
    base_keys = ['main', 'guest', 'middle1', 'middle2']
    for i, az in enumerate(az_cands):
        for b in base_keys:
            base_az = base_angles[f'{b}Azimuth']
            diff = abs(az - base_az)
            if diff < 30:
                add_q(off3_az + i, off3_az + i, (30-diff)**2 * lambda_ang)
                add_q(off4_az + i, off4_az + i, (30-diff)**2 * lambda_ang)
    for i, el in enumerate(el_cands):
        for b in base_keys:
            base_el = base_angles[f'{b}Elevation']
            diff = abs(el - base_el)
            if diff < 15:
                add_q(off3_el + i, off3_el + i, (15-diff)**2 * lambda_ang)
                add_q(off4_el + i, off4_el + i, (15-diff)**2 * lambda_ang)

    # Sign preference bias: encourage middle3 and middle4 to point on opposite sides
    sign_pref_m3 = random.choice([-1, +1])
    sign_pref_m4 = -sign_pref_m3

    lam_sign = 50.0
    for i, az in enumerate(az_cands):
        if sign_pref_m3 * az > 0:
            add_q(off3_az + i, off3_az + i, -lam_sign)

    for i, az in enumerate(az_cands):
        if sign_pref_m4 * az > 0:
            add_q(off4_az + i, off4_az + i, -lam_sign)

    # Non-overlap penalty: prevent middle3 and middle4 from having the same angle 
    penalty_same = 100.0
    for i in range(n_az):
        add_q(off3_az + i, off4_az + i, penalty_same)

    for i in range(n_el):
        add_q(off3_el + i, off4_el + i, penalty_same)

    # Solve the QUBO and extract the solution
    sampler = oj.SQASampler()
    result = sampler.sample_qubo(Q, num_reads=20)
    best = result.first.sample

    def extract_choice(offset, count):
        for i in range(count):
            if best.get(offset + i, 0) == 1:
                return i
        return None

    penalty_len_same = 80.0
    for i, (_, _, length_i) in enumerate(domain):
        for j, (_, _, length_j) in enumerate(domain):
            if length_i == length_j:
                add_q(off3_dom + i, off4_dom + j, penalty_len_same)

    i3_az = extract_choice(off3_az, n_az)
    i3_el = extract_choice(off3_el, n_el)
    i3_dom = extract_choice(off3_dom, n_dom)
    i4_az = extract_choice(off4_az, n_az)
    i4_el = extract_choice(off4_el, n_el)
    i4_dom = extract_choice(off4_dom, n_dom)

    flower3, _, length3 = domain[i3_dom] if i3_dom is not None else (None, None, None)
    flower4, _, length4 = domain[i4_dom] if i4_dom is not None else (None, None, None)
    return {
        'assignments': {'middle3': flower3, 'middle4': flower4},
        'lengths':     {'middle3': length3, 'middle4': length4},
        'angles': {
            'middle3Azimuth': az_cands[i3_az] if i3_az is not None else None,
            'middle3Elevation': el_cands[i3_el] if i3_el is not None else None,
            'middle4Azimuth': az_cands[i4_az] if i4_az is not None else None,
            'middle4Elevation': el_cands[i4_el] if i4_el is not None else None
        }
    }
