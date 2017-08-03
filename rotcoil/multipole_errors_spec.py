"""Multipole errors specification."""

import numpy as _np
import random as _random


def _get_multipole_errors_spec():
    multipole_errors = {}

    # Booster sextupole
    _dict = {}
    _dict['main'] = 2
    _dict['normal_sys_monomials'] = _np.array([8, 14])
    _dict['normal_sys_multipoles'] = _np.array([-2.5e-2, -1.5e-2])
    _dict['normal_rms_monomials'] = _np.array([3, 4, 5, 6, 7, 8, 9, 14])
    _dict['normal_rms_multipoles'] = _np.array([4, 4, 4, 4, 4, 4, 4, 4])*1e-4
    _dict['skew_sys_monomials'] = _np.array([])
    _dict['skew_sys_multipoles'] = _np.array([])
    _dict['skew_rms_monomials'] = _np.array([3, 4, 5, 6, 7, 8, 9, 14])
    _dict['skew_rms_multipoles'] = _np.array([1, 1, 1, 1, 1, 1, 1, 1])*1e-4
    multipole_errors["BS"] = _dict

    # Booster quadrupole QF
    _dict = {}
    _dict['main'] = 1
    _dict['normal_sys_monomials'] = _np.array([5, 9, 13])
    _dict['normal_sys_multipoles'] = _np.array([-1.0e-3, +1.1e-3, +8.0e-5])
    _dict['normal_rms_monomials'] = _np.array([2, 3, 4, 5, 6, 7, 8, 9, 13])
    _dict['normal_rms_multipoles'] = _np.array(
        [7, 4, 4, 4, 4, 4, 4, 4, 4])*1e-4
    _dict['skew_sys_monomials'] = _np.array([])
    _dict['skew_sys_multipoles'] = _np.array([])
    _dict['skew_rms_monomials'] = _np.array([2, 3, 4, 5, 6, 7, 8, 9, 13])
    _dict['skew_rms_multipoles'] = _np.array([1, 5, 1, 1, 1, 1, 1, 1, 1])*1e-4
    multipole_errors["BQF"] = _dict

    # Booster quadrupole QD
    _dict = {}
    _dict['main'] = 1
    _dict['normal_sys_monomials'] = _np.array([5, 9, 13])
    _dict['normal_sys_multipoles'] = _np.array([-4.7e-3, +1.2e-3, +1.2e-6])
    _dict['normal_rms_monomials'] = _np.array([2, 3, 4, 5, 6, 7, 8, 9, 13])
    _dict['normal_rms_multipoles'] = _np.array(
        [7, 4, 4, 4, 4, 4, 4, 4, 4])*1e-4
    _dict['skew_sys_monomials'] = _np.array([])
    _dict['skew_sys_multipoles'] = _np.array([])
    _dict['skew_rms_monomials'] = _np.array([2, 3, 4, 5, 6, 7, 8, 9, 13])
    _dict['skew_rms_multipoles'] = _np.array([1, 5, 1, 1, 1, 1, 1, 1, 1])*1e-4
    multipole_errors["BQD"] = _dict

    # Storage Ring sextupole S15
    _dict = {}
    _dict['main'] = 2
    _dict['normal_sys_monomials'] = _np.array([4, 6, 8, 14])
    _dict['normal_sys_multipoles'] = _np.array(
        [-7.0e-5, -1.4e-4, -2.4e-3, +1.4e-3])
    _dict['normal_rms_monomials'] = _np.array([3, 4, 5, 6, 8, 14])
    _dict['normal_rms_multipoles'] = _np.array(
        [1.5, 1.5, 1.5, 1.5, 1.5, 1.5])*1e-4
    _dict['skew_sys_monomials'] = _np.array([])
    _dict['skew_sys_multipoles'] = _np.array([])
    _dict['skew_rms_monomials'] = _np.array([3, 4, 5, 6, 8, 14])
    _dict['skew_rms_multipoles'] = _np.array(
        [0.5, 0.5, 0.5, 0.5, 0.5, 0.5])*1e-4
    multipole_errors["S15"] = _dict

    # Storage Ring quadrupole Q14
    _dict = {}
    _dict['main'] = 1
    _dict['normal_sys_monomials'] = _np.array([5, 9, 13, 17])
    _dict['normal_sys_multipoles'] = _np.array(
        [-3.9e-4, 1.7e-3, -8.0e-4, +8.5e-5])
    _dict['normal_rms_monomials'] = _np.array([2, 3, 4, 5, 9, 13, 17])
    _dict['normal_rms_multipoles'] = _np.array(
        [1.5, 1.5, 1.5, 1.5, 0, 0, 0])*1e-4
    _dict['skew_sys_monomials'] = _np.array([])
    _dict['skew_sys_multipoles'] = _np.array([])
    _dict['skew_rms_monomials'] = _np.array([2, 3, 4, 5, 9, 13, 17])
    _dict['skew_rms_multipoles'] = _np.array(
        [0.5, 0.5, 0.5, 0.5, 0, 0, 0])*1e-4
    multipole_errors["Q14"] = _dict

    # Storage Ring quadrupole Q20
    _dict = {}
    _dict['main'] = 1
    _dict['normal_sys_monomials'] = _np.array([5, 9, 13, 17])
    _dict['normal_sys_multipoles'] = _np.array(
        [-4.1e-4, 1.7e-3, -7.7e-4, +5.9e-5])
    _dict['normal_rms_monomials'] = _np.array([2, 3, 4, 5, 9, 13, 17])
    _dict['normal_rms_multipoles'] = _np.array(
        [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1, 5])*1e-4
    _dict['skew_sys_monomials'] = _np.array([])
    _dict['skew_sys_multipoles'] = _np.array([])
    _dict['skew_rms_monomials'] = _np.array([2, 3, 4, 5, 9, 13, 17])
    _dict['skew_rms_multipoles'] = _np.array(
        [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])*1e-4
    multipole_errors["Q20"] = _dict

    # Storage Ring quadrupole Q30
    _dict = {}
    _dict['main'] = 1
    _dict['normal_sys_monomials'] = _np.array([5, 9, 13, 17])
    _dict['normal_sys_multipoles'] = _np.array(
        [-4.3e-4, 1.8e-3, -8.1e-4, +7.2e-5])
    _dict['normal_rms_monomials'] = _np.array([2, 3, 4, 5, 9, 13, 17])
    _dict['normal_rms_multipoles'] = _np.array(
        [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1, 5])*1e-4
    _dict['skew_sys_monomials'] = _np.array([])
    _dict['skew_sys_multipoles'] = _np.array([])
    _dict['skew_rms_monomials'] = _np.array([2, 3, 4, 5, 9, 13, 17])
    _dict['skew_rms_multipoles'] = _np.array(
        [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])*1e-4
    multipole_errors["Q30"] = _dict

    return multipole_errors


def _get_magnet_multipole_errors_spec(magnet_name):
    multipole_errors = _get_multipole_errors_spec()

    magnet_key = None
    if magnet_name in multipole_errors.keys():
        magnet_key = magnet_name
    else:
        for k in multipole_errors.keys():
            if magnet_name.startswith(k):
                magnet_key = k
                break

    if magnet_key is None:
        return None
    else:
        magnet_spec = multipole_errors[magnet_key]
        return magnet_spec


def _residual_field(r0, x, n, sys_monomials, sys_relative_multipoles_at_r0,
                    rms_monomials, rms_relative_multipoles_at_r0):
    nr_samples = 5000
    gauss_trunc = 1

    # Systematic residual
    sys_residue = _np.zeros(len(x))
    for i in range(len(sys_monomials)):
        sys_residue = (
            sys_residue +
            1*sys_relative_multipoles_at_r0[i]*(x/r0)**(sys_monomials[i]-n))

    size = len(rms_relative_multipoles_at_r0)*nr_samples
    rnd_grid = _np.array([])

    # Making the random normal distribution
    while (len(rnd_grid) < size):
        randomgauss = _random.gauss(0, 1)
        if (abs(randomgauss) > gauss_trunc):
            randomgauss = []
        rnd_grid = _np.append(rnd_grid,  randomgauss)
    rnd_grid = rnd_grid.reshape(nr_samples, int(size/nr_samples))

    max_residue = sys_residue
    min_residue = sys_residue

    # Use rows of random grid for calculate the relative rms and residual field
    for j in range(nr_samples):
        rnd_vector = rnd_grid[j, :]
        rnd_relative_rms = (rms_relative_multipoles_at_r0)*rnd_vector
        rms_residue = 0
        for i in range(len(rms_monomials)):
            rms_residue = (
                rms_residue +
                1*rnd_relative_rms[i]*(x/r0)**(rms_monomials[i]-n))

        residue_field = sys_residue + rms_residue

        # Maximum residual values
        max_residue = _np.maximum(residue_field,  max_residue)

        # Minimum residual values
        min_residue = _np.minimum(residue_field,  min_residue)

    return sys_residue,  max_residue,  min_residue


def normal_residual_field(r0, x, magnet_name):
    """Get normal residual field limits.

    Args:
        r0 (float): reference radius [m].
        x (array): transversal position values [m].
        magnet_name (str): magnet name.

    Returns:
        sys_residue (array): systematic error values [T].
        min_residue (array): minimum error limit [T].
        max_residue (array): maximum error limit [T].
    """
    multipole_errors = _get_magnet_multipole_errors_spec(magnet_name)

    if multipole_errors is None:
        return None,  None,  None

    else:
        n = multipole_errors['main']
        normal_sys_monomials = multipole_errors['normal_sys_monomials']
        normal_sys_multipoles = multipole_errors['normal_sys_multipoles']
        normal_rms_monomials = multipole_errors['normal_rms_monomials']
        normal_rms_multipoles = multipole_errors['normal_rms_multipoles']
        sys_residue,  max_residue,  min_residue = _residual_field(
            r0, x, n, normal_sys_monomials, normal_sys_multipoles,
            normal_rms_monomials, normal_rms_multipoles)

        return sys_residue,  min_residue, max_residue


def skew_residual_field(r0, x, magnet_name):
    """Get skew residual field limits.

    Args:
        r0 (float): reference radius [m].
        x (array): transversal position values [m].
        magnet_name (str): magnet name.

    Returns:
        sys_residue (array): systematic error values [T].
        min_residue (array): minimum error limit [T].
        max_residue (array): maximum error limit [T].
    """
    multipole_errors = _get_magnet_multipole_errors_spec(magnet_name)

    if multipole_errors is None:
        return None,  None,  None

    else:
        n = multipole_errors['main']
        skew_sys_monomials = multipole_errors['skew_sys_monomials']
        skew_sys_multipoles = multipole_errors['skew_sys_multipoles']
        skew_rms_monomials = multipole_errors['skew_rms_monomials']
        skew_rms_multipoles = multipole_errors['skew_rms_multipoles']
        sys_residue,  max_residue,  min_residue = _residual_field(
            r0, x, n, skew_sys_monomials, skew_sys_multipoles,
            skew_rms_monomials, skew_rms_multipoles)

        return sys_residue,  min_residue, max_residue