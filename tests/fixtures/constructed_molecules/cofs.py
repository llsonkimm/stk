import stk
import pytest


@pytest.fixture(scope='function')
def tmp_honeycomb(tmp_amine2, tmp_aldehyde3):
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine2, tmp_aldehyde3],
        topology_graph=stk.cof.Honeycomb((3, 3, 1))
    )


@pytest.fixture(scope='function')
def tmp_periodic_honeycomb(tmp_amine2, tmp_aldehyde3):
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine2, tmp_aldehyde3],
        topology_graph=stk.cof.Honeycomb((3, 3, 1), True)
    )


@pytest.fixture(scope='function')
def tmp_kagome(tmp_amine2, tmp_aldehyde4):
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine2, tmp_aldehyde4],
        topology_graph=stk.cof.Kagome((3, 3, 1))
    )


@pytest.fixture(scope='function')
def tmp_periodic_kagome(tmp_amine2, tmp_aldehyde4):
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine2, tmp_aldehyde4],
        topology_graph=stk.cof.Kagome((3, 3, 1), True)
    )


@pytest.fixture(scope='function')
def tmp_hexagonal(tmp_amine2, tmp_aldehyde6):
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine2, tmp_aldehyde6],
        topology_graph=stk.cof.Hexagonal((3, 3, 1))
    )


@pytest.fixture(scope='function')
def tmp_periodic_hexagonal(tmp_amine2, tmp_aldehyde6):
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine2, tmp_aldehyde6],
        topology_graph=stk.cof.Hexagonal((3, 3, 1), True)
    )


@pytest.fixture(scope='function')
def tmp_square(tmp_amine2, tmp_aldehyde4):
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine2, tmp_aldehyde4],
        topology_graph=stk.cof.Square((3, 3, 1))
    )


@pytest.fixture(scope='function')
def tmp_periodic_square(tmp_amine2, tmp_aldehyde4):
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine2, tmp_aldehyde4],
        topology_graph=stk.cof.Square((3, 3, 1), True)
    )


@pytest.fixture(scope='function')
def tmp_linkerless_honeycomb(tmp_amine3, tmp_aldehyde3):
    topology_graph = stk.cof.LinkerlessHoneycomb((3, 3, 1))
    num_verts = len(topology_graph.vertices)
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine3, tmp_aldehyde3],
        topology_graph=topology_graph,
        building_block_vertices={
            tmp_amine3: topology_graph.vertices[:num_verts//2],
            tmp_aldehyde3: topology_graph.vertices[num_verts//2:]
        }
    )


@pytest.fixture(scope='function')
def tmp_periodic_linkerless_honeycomb(tmp_amine3, tmp_aldehyde3):
    topology_graph = stk.cof.LinkerlessHoneycomb((3, 3, 1), True)
    num_verts = len(topology_graph.vertices)
    return stk.ConstructedMolecule(
        building_blocks=[tmp_amine3, tmp_aldehyde3],
        topology_graph=topology_graph,
        building_block_vertices={
            tmp_amine3: topology_graph.vertices[:num_verts//2],
            tmp_aldehyde3: topology_graph.vertices[num_verts//2:]
        }
    )
