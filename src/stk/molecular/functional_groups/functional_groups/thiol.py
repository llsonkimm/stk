from .. import FunctionalGroup_


class Thiol(FunctionalGroup_):
    """
    Represents a thiol functional group.


    The structure of the functional group is given by the pseudo-SMILES
    ``[atom][sulfur][hydrogen]``.

    """

    def __init__(self, sulfur, hydrogen, atom, bonders, deleters):
        atom_map = {
            sulfur.id: sulfur.clone(),
            hydrogen.id: hydrogen.clone(),
            atom.id: atom.clone(),
        }
        self._sulfur = atom_map[sulfur]
        self._hydrogen = atom_map[hydrogen]
        self._atom = atom_map[atom]
        super()._init(
            atoms=tuple(atom_map.values()),
            bonders=tuple(atom_map[a.id] for a in bonders),
            deleters=tuple(atom_map[a.id] for a in deleters),
        )

    def get_sulfur(self):
        return self._sulfur.clone()

    def get_hydrogen(self):
        return self._hydrogen.clone()

    def get_atom(self):
        return self._atom.clone()

    def clone(self, atom_map=None):
        if atom_map is None:
            atom_map = {}
        else:
            atom_map = dict(atom_map)

        atoms = (self._sulfur, self._hydrogen, self._atom)
        for atom in atoms:
            if atom.id not in atom_map:
                atom_map[atom.id] = atom.clone()

        clone = super().clone(atom_map)
        clone._sulfur = atom_map[self._sulfur.id]
        clone._hydrogen = atom_map[self._hydrogen.id]
        clone._atom = atom_map[self._atom.id]
        return clone

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'{self._sulfur}, {self._hydrogen}, {self._atom}, '
            f'bonders={self._bonders}, deleters={self._deleters})'
        )
