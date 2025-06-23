import openjij as oj
import random


def run_ikebana_qa_3d(
    W,
    H,
    flower_lengths,
    candidate_lengths,
    forced_flower=None,
    front_azimuth=0,
    front_elevation=0,
):
    # Parameters & Limits
    LIM = 2 * (W + H)

    # Angle Candidate Lists
    main_azimuth_candidates = [front_azimuth + delta for delta in [-20, -10, 0, 10, 20]]
    main_elevation_candidates = [front_elevation + delta for delta in [-10, 0, 10]]
    guest_azimuth_candidates = [front_azimuth]
    guest_elevation_candidates = [front_elevation + 45]
    middle_azimuth_candidates = [front_azimuth + delta for delta in [-50, -40, 40, 50]]
    middle_elevation_candidates = [
        front_elevation + delta for delta in [30, 40, 50, 60, 70]
    ]

    flower_list = list(flower_lengths.keys())

    # Build Domain for Flower Length Choices
    def build_domain():
        domain = []
        for flower in flower_list:
            lengths = candidate_lengths[flower]
            for cand_idx, length_val in enumerate(lengths):
                domain.append((flower, cand_idx, length_val))
        return domain

    domain_main = build_domain()
    domain_guest = build_domain()
    domain_middle1 = build_domain()
    domain_middle2 = build_domain()

    n_ext_main = len(domain_main)
    n_ext_guest = len(domain_guest)
    n_ext_middle1 = len(domain_middle1)
    n_ext_middle2 = len(domain_middle2)

    # Initialize QUBO Matrix
    Q = {}

    def add_q(i, j, val):
        if i > j:
            i, j = j, i
        Q[(i, j)] = Q.get((i, j), 0.0) + val

    # Compute Variable Offsets
    offset = 0
    offset_main_az = offset
    n_main_az = len(main_azimuth_candidates)
    offset += n_main_az
    offset_main_el = offset
    n_main_el = len(main_elevation_candidates)
    offset += n_main_el
    offset_guest_az = offset
    n_guest_az = len(guest_azimuth_candidates)
    offset += n_guest_az
    offset_guest_el = offset
    n_guest_el = len(guest_elevation_candidates)
    offset += n_guest_el

    offset_middle1_az = offset
    n_middle1_az = len(middle_azimuth_candidates)
    offset += n_middle1_az
    offset_middle1_el = offset
    n_middle1_el = len(middle_elevation_candidates)
    offset += n_middle1_el

    offset_middle2_az = offset
    n_middle2_az = len(middle_azimuth_candidates)
    offset += n_middle2_az
    offset_middle2_el = offset
    n_middle2_el = len(middle_elevation_candidates)
    offset += n_middle2_el

    offset_ext_main = offset
    offset += n_ext_main
    offset_ext_guest = offset
    offset += n_ext_guest
    offset_ext_middle1 = offset
    offset += n_ext_middle1
    offset_ext_middle2 = offset
    offset += n_ext_middle2

    # One‐Hot Constraints
    def add_strict_one_hot(offset, n, A=100.0):
        for i in range(n):
            idx_i = offset + i
            add_q(idx_i, idx_i, A)  # ここで A を追加
            # -2A * x_i を加える
            add_q(idx_i, idx_i, -2 * A)
            # 以下、ペアごとに 2A を加える
            for j in range(i + 1, n):
                idx_j = offset + j
                add_q(idx_i, idx_j, 2 * A)

    add_strict_one_hot(offset_main_az, n_main_az, 60)
    add_strict_one_hot(offset_main_el, n_main_el, 60)
    add_strict_one_hot(offset_guest_az, n_guest_az, 50)
    add_strict_one_hot(offset_guest_el, n_guest_el, 50)
    add_strict_one_hot(offset_middle1_az, n_middle1_az, 50)
    add_strict_one_hot(offset_middle1_el, n_middle1_el, 50)
    add_strict_one_hot(offset_middle2_az, n_middle2_az, 50)
    add_strict_one_hot(offset_middle2_el, n_middle2_el, 50)
    add_strict_one_hot(offset_ext_main, n_ext_main, 50)
    add_strict_one_hot(offset_ext_guest, n_ext_guest, 50)
    add_strict_one_hot(offset_ext_middle1, n_ext_middle1, 50)
    add_strict_one_hot(offset_ext_middle2, n_ext_middle2, 50)

    # No‐Duplicate‐Flower Constraints
    penalty_same_flower = 50
    for i, (f1, _, _) in enumerate(domain_main):
        for j, (f2, _, _) in enumerate(domain_guest):
            if f1 == f2:
                add_q(
                    offset_ext_main + i, offset_ext_guest + j, 2 * penalty_same_flower
                )
        for j, (f2, _, _) in enumerate(domain_middle1):
            if f1 == f2:
                add_q(
                    offset_ext_main + i, offset_ext_middle1 + j, 2 * penalty_same_flower
                )

    for i, (f1, _, _) in enumerate(domain_guest):
        for j, (f2, _, _) in enumerate(domain_middle1):
            if f1 == f2:
                add_q(
                    offset_ext_guest + i,
                    offset_ext_middle1 + j,
                    2 * penalty_same_flower,
                )

    # Forced‐Flower Constraint
    if forced_flower is not None and forced_flower in flower_list:
        A_forced = 50
        for i, (f, _, _) in enumerate(domain_main):
            if f == forced_flower:
                add_q(offset_ext_main + i, offset_ext_main + i, -A_forced)
        for i, (f, _, _) in enumerate(domain_guest):
            if f == forced_flower:
                add_q(offset_ext_guest + i, offset_ext_guest + i, -A_forced)
        for i, (f, _, _) in enumerate(domain_middle1):
            if f == forced_flower:
                add_q(offset_ext_middle1 + i, offset_ext_middle1 + i, -A_forced)
        for i, (f, _, _) in enumerate(domain_middle2):
            if f == forced_flower:
                add_q(offset_ext_middle2 + i, offset_ext_middle2 + i, -A_forced)

    # Main branch length limit
    lambda_main_len = 1.0
    for i, (f, cand_idx, length_val) in enumerate(domain_main):
        if length_val > LIM:
            cost = (length_val - LIM) ** 2
            add_q(offset_ext_main + i, offset_ext_main + i, cost * lambda_main_len)

    # Guest branch proportional length
    lambda_guest_len = 1.0
    for i, (_, _, length_m) in enumerate(domain_main):
        for j, (_, _, length_g) in enumerate(domain_guest):
            cost = (length_g - (length_m / 3.0)) ** 2
            add_q(offset_ext_main + i, offset_ext_guest + j, cost * lambda_guest_len)

    # Main branch angle cost
    penalty_main_angle = 0.5
    for i, az in enumerate(main_azimuth_candidates):
        idx = offset_main_az + i
        cost = (az) ** 2
        add_q(idx, idx, cost * penalty_main_angle)
    for i, el in enumerate(main_elevation_candidates):
        idx = offset_main_el + i
        cost = (el) ** 2
        add_q(idx, idx, cost * penalty_main_angle)

    # Triangle‐shape angle constraint
    lambda_triangle = 10.0
    allowed_threshold = 45.0
    for i, main_az in enumerate(main_azimuth_candidates):
        for j, mid_az in enumerate(middle_azimuth_candidates):
            diff = abs(mid_az - main_az)
            if diff > allowed_threshold:
                cost = (diff - allowed_threshold) ** 2
                # 適用を両方の中間枝へ
                add_q(offset_main_az + i, offset_middle1_az + j, cost * lambda_triangle)
                add_q(offset_main_az + i, offset_middle2_az + j, cost * lambda_triangle)

    lambda_side = 10.0
    for j, middle_el in enumerate(middle_elevation_candidates):
        if middle_el < -45:
            cost = (-45 - middle_el) ** 2
            add_q(offset_middle1_el + j, offset_middle1_el + j, cost * lambda_side)
            add_q(offset_middle2_el + j, offset_middle2_el + j, cost * lambda_side)
        elif middle_el > 45:
            cost = (middle_el - 45) ** 2
            add_q(offset_middle1_el + j, offset_middle1_el + j, cost * lambda_side)
            add_q(offset_middle2_el + j, offset_middle2_el + j, cost * lambda_side)

    # Middle branch shorter than main
    lambda_mid = 10.0
    for i, (fM, cand_idx_m, length_m) in enumerate(domain_main):
        for j, (fC, cand_idx_c, length_c) in enumerate(domain_middle1):
            if length_c >= length_m:
                penalty = (length_c - length_m) ** 2
                add_q(offset_ext_main + i, offset_ext_middle1 + j, penalty * lambda_mid)
        for j, (fC, cand_idx_c, length_c) in enumerate(domain_middle2):
            if length_c >= length_m:
                penalty = (length_c - length_m) ** 2
                add_q(offset_ext_main + i, offset_ext_middle2 + j, penalty * lambda_mid)

    # Reward for main branch near LIM
    lambda_main_reward = 0.01
    for i, (f, cand_idx, length_val) in enumerate(domain_main):
        if length_val <= LIM:
            add_q(
                offset_ext_main + i,
                offset_ext_main + i,
                (LIM - length_val) ** 2 * lambda_main_reward,
            )

    # Encourage middle1 to go left/right and middle2 to go in the opposite direction
    sign_pref_m1 = random.choice([-1, +1])
    sign_pref_m2 = -sign_pref_m1

    lam_sign = 45.0
    for i, az in enumerate(middle_azimuth_candidates):
        if sign_pref_m1 * az > 0:
            add_q(offset_middle1_az + i, offset_middle1_az + i, -lam_sign)

    for i, az in enumerate(middle_azimuth_candidates):
        if sign_pref_m2 * az > 0:
            add_q(offset_middle2_az + i, offset_middle2_az + i, -lam_sign)

    # Add penalties when any two branches have equal length
    penalty_equal_length = 45
    branches = [
        ("main", offset_ext_main, domain_main),
        ("guest", offset_ext_guest, domain_guest),
        ("middle1", offset_ext_middle1, domain_middle1),
        ("middle2", offset_ext_middle2, domain_middle2),
    ]

    for b1_idx in range(len(branches)):
        name1, off1, domain1 = branches[b1_idx]
        for b2_idx in range(b1_idx + 1, len(branches)):
            name2, off2, domain2 = branches[b2_idx]
            for i, cand1 in enumerate(domain1):
                for j, cand2 in enumerate(domain2):
                    length1 = cand1[2]
                    length2 = cand2[2]
                    if length1 == length2:
                        add_q(off1 + i, off2 + j, penalty_equal_length)

    #  Silver‐ratio penalty between middle1 & middle2
    lambda_silver = 5.0
    silver_ratio = 1.414

    for i, (_, _, L_middle1) in enumerate(domain_middle1):
        for j, (_, _, L_middle2) in enumerate(domain_middle2):
            diff = L_middle2 - silver_ratio * L_middle1
            penalty = lambda_silver * (diff) ** 2
            add_q(offset_ext_middle1 + i, offset_ext_middle2 + j, penalty)

    #  Solve QUBO & Extract Solution
    sampler = oj.SQASampler()
    result = sampler.sample_qubo(Q, num_reads=20)
    best = result.first
    energy = best.energy
    solution = best.sample

    def get_choice(sol, off, n):
        for i in range(n):
            if sol.get(off + i, 0) == 1:
                return i
        return None

    i_main_az = get_choice(solution, offset_main_az, n_main_az)
    i_main_el = get_choice(solution, offset_main_el, n_main_el)
    chosen_main_az = (
        main_azimuth_candidates[i_main_az] if i_main_az is not None else None
    )
    chosen_main_el = (
        main_elevation_candidates[i_main_el] if i_main_el is not None else None
    )

    i_guest_az = get_choice(solution, offset_guest_az, n_guest_az)
    i_guest_el = get_choice(solution, offset_guest_el, n_guest_el)
    chosen_guest_az = (
        guest_azimuth_candidates[i_guest_az] if i_guest_az is not None else None
    )
    chosen_guest_el = (
        guest_elevation_candidates[i_guest_el] if i_guest_el is not None else None
    )

    i_middle1_az = get_choice(solution, offset_middle1_az, n_middle1_az)
    i_middle1_el = get_choice(solution, offset_middle1_el, n_middle1_el)
    chosen_middle1_az = (
        middle_azimuth_candidates[i_middle1_az] if i_middle1_az is not None else None
    )
    chosen_middle1_el = (
        middle_elevation_candidates[i_middle1_el] if i_middle1_el is not None else None
    )

    i_middle2_az = get_choice(solution, offset_middle2_az, n_middle2_az)
    i_middle2_el = get_choice(solution, offset_middle2_el, n_middle2_el)
    chosen_middle2_az = (
        middle_azimuth_candidates[i_middle2_az] if i_middle2_az is not None else None
    )
    chosen_middle2_el = (
        middle_elevation_candidates[i_middle2_el] if i_middle2_el is not None else None
    )

    i_ext_main = get_choice(solution, offset_ext_main, n_ext_main)
    i_ext_guest = get_choice(solution, offset_ext_guest, n_ext_guest)
    i_ext_middle1 = get_choice(solution, offset_ext_middle1, n_ext_middle1)
    i_ext_middle2 = get_choice(solution, offset_ext_middle2, n_ext_middle2)

    chosen_main_flower, _, chosen_mainLen = (
        domain_main[i_ext_main] if i_ext_main is not None else (None, None, None)
    )
    chosen_guest_flower, _, chosen_guestLen = (
        domain_guest[i_ext_guest] if i_ext_guest is not None else (None, None, None)
    )
    chosen_middle1_flower, _, chosen_middle1Len = (
        domain_middle1[i_ext_middle1]
        if i_ext_middle1 is not None
        else (None, None, None)
    )
    chosen_middle2_flower, _, chosen_middle2Len = (
        domain_middle2[i_ext_middle2]
        if i_ext_middle2 is not None
        else (None, None, None)
    )

    return {
        "energy": energy,
        "assignments": {
            "main": chosen_main_flower,
            "guest": chosen_guest_flower,
            "middle1": chosen_middle1_flower,
            "middle2": chosen_middle2_flower,
        },
        "mainLen": chosen_mainLen,
        "guestLen": chosen_guestLen,
        "middle1Len": chosen_middle1Len,
        "middle2Len": chosen_middle2Len,
        "mainAzimuth": chosen_main_az,
        "mainElevation": chosen_main_el,
        "guestAzimuth": chosen_guest_az,
        "guestElevation": chosen_guest_el,
        "middle1Azimuth": chosen_middle1_az,
        "middle1Elevation": chosen_middle1_el,
        "middle2Azimuth": chosen_middle2_az,
        "middle2Elevation": chosen_middle2_el,
        "flowers": flower_lengths,
        "Q": {str(k): v for k, v in Q.items()},
    }


if __name__ == "__main__":
    flower_lengths = {
        "桜": 0.4,
        "リアトリス": 0.4,
        "ディル": 0.4,
        "モルセラ": 0.25,
        "バラ": 0.25,
        "牡丹": 0.25,
        "ユリ": 0.25,
    }
    candidate_lengths = {
        "桜": [60, 50, 30],
        "リアトリス": [60, 50, 30],
        "ディル": [60, 50, 30],
        "モルセラ": [60, 50, 30],
        "バラ": [23, 20, 15],
        "牡丹": [23, 17, 15],
        "ユリ": [23, 17, 15],
    }

    forced = ""
    for vase, (W, H) in [("筒形花器", (10, 20)), ("皿型花器", (10, 15))]:
        result = run_ikebana_qa_3d(
            W,
            H,
            flower_lengths,
            candidate_lengths,
            forced_flower=forced,
            front_azimuth=0,
            front_elevation=0,
        )

    print("=== Best solution ===")
    print("Energy =", result["energy"])
    print("assignments =", result["assignments"])
    print(
        "主枝: Len =",
        result["mainLen"],
        "Azimuth =",
        result["mainAzimuth"],
        "Elevation =",
        result["mainElevation"],
    )
    print(
        "客枝: Len =",
        result["guestLen"],
        "Azimuth =",
        result["guestAzimuth"],
        "Elevation =",
        result["guestElevation"],
    )
    print(
        "中間枝1: Len =",
        result["middle1Len"],
        "Azimuth =",
        result["middle1Azimuth"],
        "Elevation =",
        result["middle1Elevation"],
    )
    print(
        "中間枝2: Len =",
        result["middle2Len"],
        "Azimuth =",
        result["middle2Azimuth"],
        "Elevation =",
        result["middle2Elevation"],
    )
    print("flowers:", result["flowers"])
