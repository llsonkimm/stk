import numpy as np


def has_same_structure(molecule1, molecule2):
    assert np.all(np.equal(
        molecule1.get_position_matrix(),
        molecule2.get_position_matrix(),
    ))


def get_displacement_vector(molecule, start_atom, end_atom):
    """
    Get the displacement vector between `start_atom` and `end_atom`.

    """

    position1, position2 = (
        molecule.get_atomic_positions((start_atom, end_atom))
    )
    return position2 - position1


def get_num_atom_ids(molecule, get_atom_ids):
    atom_ids = get_atom_ids(molecule)
    if atom_ids is None:
        return molecule.get_num_atoms()
    else:
        return len(tuple(atom_ids))
