import unittest

import numpy as np
import openmdao.api as om
from common_methods import CommonMethods
from fake_aero import (
    AeroBuilder,
    AeroCouplingComp,
    AeroMeshComp,
    AeroPostCouplingComp,
    AeroPreCouplingComp,
)
from fake_geometry import Geometry, GeometryBuilder
from fake_ldxfer import DispXferComp, LDXferBuilder, LoadXferComp
from fake_struct import (
    StructBuilder,
    StructCouplingComp,
    StructMeshComp,
    StructPostCouplingComp,
    StructPreCouplingComp,
)
from mpi4py import MPI

from mphys import MPhysVariables
from mphys.scenarios.aerostructural import (
    CouplingAeroStructural,
    ScenarioAeroStructural,
)
from mphys.scenarios.geo_disp import GeoDisp


class TestScenarioAeroStructural(unittest.TestCase):
    def setUp(self):
        self.common = CommonMethods()
        self.prob = om.Problem()

        aero_builder = AeroBuilder()
        struct_builder = StructBuilder()
        ldxfer_builder = LDXferBuilder(aero_builder, struct_builder)

        aero_builder.initialize(MPI.COMM_WORLD)
        struct_builder.initialize(MPI.COMM_WORLD)
        ldxfer_builder.initialize(MPI.COMM_WORLD)

        self.prob.model.add_subsystem(
            "aero_mesh", aero_builder.get_mesh_coordinate_subsystem()
        )
        self.prob.model.add_subsystem(
            "struct_mesh", struct_builder.get_mesh_coordinate_subsystem()
        )
        self.prob.model.add_subsystem(
            "scenario",
            ScenarioAeroStructural(
                aero_builder=aero_builder,
                struct_builder=struct_builder,
                ldxfer_builder=ldxfer_builder,
            ),
        )
        self.prob.model.connect(
            f"aero_mesh.{MPhysVariables.Aerodynamics.Surface.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Aerodynamics.Surface.COORDINATES_INITIAL}",
        )

        self.prob.model.connect(
            f"struct_mesh.{MPhysVariables.Structures.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Structures.COORDINATES}",
        )
        self.prob.setup()

    def test_run_model(self):
        self.common.test_run_model(self)

    def test_scenario_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.aero_pre, AeroPreCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_pre, StructPreCouplingComp
        )
        self.assertIsInstance(self.prob.model.scenario.coupling, CouplingAeroStructural)
        self.assertIsInstance(self.prob.model.scenario.aero_post, AeroPostCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_post, StructPostCouplingComp
        )

    def test_scenario_subsystem_order(self):
        expected_order = [
            "aero_pre",
            "struct_pre",
            "coupling",
            "aero_post",
            "struct_post",
        ]
        self.common.test_subsystem_order(self, self.prob.model.scenario, expected_order)

    def test_coupling_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.coupling.aero, AeroCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.coupling.struct, StructCouplingComp
        )
        self.assertIsInstance(self.prob.model.scenario.coupling.disp_xfer, DispXferComp)
        self.assertIsInstance(self.prob.model.scenario.coupling.load_xfer, LoadXferComp)
        self.assertIsInstance(self.prob.model.scenario.coupling.geo_disp, GeoDisp)

    def test_coupling_subsystem_order(self):
        expected_order = ["disp_xfer", "geo_disp", "aero", "load_xfer", "struct"]
        self.common.test_subsystem_order(
            self, self.prob.model.scenario.coupling, expected_order
        )

    def test_no_autoivcs(self):
        self.common.test_no_autoivcs(self)


class TestScenarioAeroStructuralParallel(unittest.TestCase):
    def setUp(self):
        self.common = CommonMethods()
        self.prob = om.Problem()

        aero_builder = AeroBuilder()
        struct_builder = StructBuilder()
        ldxfer_builder = LDXferBuilder(aero_builder, struct_builder)

        self.prob.model.add_subsystem(
            "scenario",
            ScenarioAeroStructural(
                aero_builder=aero_builder,
                struct_builder=struct_builder,
                ldxfer_builder=ldxfer_builder,
                in_MultipointParallel=True,
            ),
        )
        self.prob.setup()

    def test_run_model(self):
        self.common.test_run_model(self)

    def test_scenario_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.aero_mesh, AeroMeshComp)
        self.assertIsInstance(self.prob.model.scenario.struct_mesh, StructMeshComp)
        self.assertIsInstance(self.prob.model.scenario.aero_pre, AeroPreCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_pre, StructPreCouplingComp
        )
        self.assertIsInstance(self.prob.model.scenario.coupling, CouplingAeroStructural)
        self.assertIsInstance(self.prob.model.scenario.aero_post, AeroPostCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_post, StructPostCouplingComp
        )

    def test_no_autoivcs(self):
        self.common.test_no_autoivcs(self)

    def test_scenario_subsystem_order(self):
        expected_order = [
            "aero_mesh",
            "struct_mesh",
            "aero_pre",
            "struct_pre",
            "coupling",
            "aero_post",
            "struct_post",
        ]
        self.common.test_subsystem_order(self, self.prob.model.scenario, expected_order)

    def test_coupling_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.coupling.aero, AeroCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.coupling.struct, StructCouplingComp
        )
        self.assertIsInstance(self.prob.model.scenario.coupling.disp_xfer, DispXferComp)
        self.assertIsInstance(self.prob.model.scenario.coupling.load_xfer, LoadXferComp)
        self.assertIsInstance(self.prob.model.scenario.coupling.geo_disp, GeoDisp)

    def test_coupling_subsystem_order(self):
        expected_order = ["disp_xfer", "geo_disp", "aero", "load_xfer", "struct"]
        self.common.test_subsystem_order(
            self, self.prob.model.scenario.coupling, expected_order
        )


class TestScenarioAeroStructuralParallelWithGeometry(unittest.TestCase):
    def setUp(self):
        self.common = CommonMethods()
        self.prob = om.Problem()

        aero_builder = AeroBuilder()
        struct_builder = StructBuilder()
        ldxfer_builder = LDXferBuilder(aero_builder, struct_builder)
        geometry_builder = GeometryBuilder(
            ["aero", "struct"], [aero_builder, struct_builder]
        )

        self.prob.model.add_subsystem(
            "scenario",
            ScenarioAeroStructural(
                aero_builder=aero_builder,
                struct_builder=struct_builder,
                ldxfer_builder=ldxfer_builder,
                geometry_builder=geometry_builder,
                in_MultipointParallel=True,
            ),
        )
        self.prob.setup()

    def test_run_model(self):
        self.common.test_run_model(self)

    def test_scenario_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.aero_mesh, AeroMeshComp)
        self.assertIsInstance(self.prob.model.scenario.struct_mesh, StructMeshComp)
        self.assertIsInstance(self.prob.model.scenario.geometry, Geometry)
        self.assertIsInstance(self.prob.model.scenario.aero_pre, AeroPreCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_pre, StructPreCouplingComp
        )
        self.assertIsInstance(self.prob.model.scenario.coupling, CouplingAeroStructural)
        self.assertIsInstance(self.prob.model.scenario.aero_post, AeroPostCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_post, StructPostCouplingComp
        )

    def test_no_autoivcs(self):
        self.common.test_no_autoivcs(self)

    def test_scenario_subsystem_order(self):
        expected_order = [
            "aero_mesh",
            "struct_mesh",
            "geometry",
            "aero_pre",
            "struct_pre",
            "coupling",
            "aero_post",
            "struct_post",
        ]
        self.common.test_subsystem_order(self, self.prob.model.scenario, expected_order)

    def test_coupling_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.coupling.aero, AeroCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.coupling.struct, StructCouplingComp
        )
        self.assertIsInstance(self.prob.model.scenario.coupling.disp_xfer, DispXferComp)
        self.assertIsInstance(self.prob.model.scenario.coupling.load_xfer, LoadXferComp)
        self.assertIsInstance(self.prob.model.scenario.coupling.geo_disp, GeoDisp)

    def test_coupling_subsystem_order(self):
        expected_order = ["disp_xfer", "geo_disp", "aero", "load_xfer", "struct"]
        self.common.test_subsystem_order(
            self, self.prob.model.scenario.coupling, expected_order
        )


class StructPostCouplingCompForNoCoupling(om.ExplicitComponent):
    def setup(self):
        self.coords_name = MPhysVariables.Structures.COORDINATES
        self.add_input("prestate_struct", tags=["mphys_coupling"])
        self.add_input(self.coords_name, shape_by_conn=True, tags=["mphys_coordinates"])
        self.add_output("func_struct", val=1.0, tags=["mphys_result"])

    def compute(self, inputs, outputs):
        outputs["func_struct"] = np.sum(
            inputs["prestate_struct"] + inputs[self.coords_name]
        )


class StructBuilderNoCoupling(StructBuilder):
    def get_post_coupling_subsystem(self, scenario_name=None):
        return StructPostCouplingCompForNoCoupling()


class TestScenarioAeroStructuralAeroOnlyInCoupling(unittest.TestCase):
    def setUp(self):
        self.common = CommonMethods()
        self.prob = om.Problem()

        aero_builder = AeroBuilder()
        struct_builder = StructBuilderNoCoupling()
        ldxfer_builder = LDXferBuilder(aero_builder, struct_builder)

        aero_builder.initialize(MPI.COMM_WORLD)
        struct_builder.initialize(MPI.COMM_WORLD)
        ldxfer_builder.initialize(MPI.COMM_WORLD)

        self.prob.model.add_subsystem(
            "aero_mesh", aero_builder.get_mesh_coordinate_subsystem()
        )
        self.prob.model.add_subsystem(
            "struct_mesh", struct_builder.get_mesh_coordinate_subsystem()
        )
        self.prob.model.add_subsystem(
            "scenario",
            ScenarioAeroStructural(
                aero_builder=aero_builder,
                struct_builder=struct_builder,
                ldxfer_builder=ldxfer_builder,
                coupling_group_type="aerodynamics_only",
            ),
        )
        self.prob.model.connect(
            f"aero_mesh.{MPhysVariables.Aerodynamics.Surface.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Aerodynamics.Surface.COORDINATES_INITIAL}",
        )
        self.prob.model.connect(
            f"aero_mesh.{MPhysVariables.Aerodynamics.Surface.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Aerodynamics.Surface.COORDINATES}",
        )

        self.prob.model.connect(
            f"struct_mesh.{MPhysVariables.Structures.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Structures.COORDINATES}",
        )
        self.prob.setup()

    def test_run_model(self):
        self.common.test_run_model(self)

    def test_scenario_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.aero_pre, AeroPreCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_pre, StructPreCouplingComp
        )
        self.assertIsInstance(self.prob.model.scenario.aero, AeroCouplingComp)
        self.assertIsInstance(self.prob.model.scenario.aero_post, AeroPostCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_post, StructPostCouplingCompForNoCoupling
        )

    def test_scenario_subsystem_order(self):
        expected_order = ["aero_pre", "struct_pre", "aero", "aero_post", "struct_post"]
        self.common.test_subsystem_order(self, self.prob.model.scenario, expected_order)

    def test_no_autoivcs(self):
        self.common.test_no_autoivcs(self)


class AeroPostCouplingCompForNoCoupling(om.ExplicitComponent):
    def setup(self):
        self.coords_name = MPhysVariables.Aerodynamics.Surface.COORDINATES

        self.add_input("prestate_aero", tags=["mphys_coupling"])
        self.add_input(self.coords_name, shape_by_conn=True, tags=["mphys_coordinates"])
        self.add_output("func_aero", val=1.0, tags=["mphys_result"])

    def compute(self, inputs, outputs):
        outputs["func_aero"] = np.sum(
            inputs["prestate_aero"] + inputs[self.coords_name]
        )


class AeroBuilderNoCoupling(AeroBuilder):
    def get_post_coupling_subsystem(self, scenario_name=None):
        return AeroPostCouplingCompForNoCoupling()


class TestScenarioAeroStructuralNoCoupling(unittest.TestCase):
    def setUp(self):
        self.common = CommonMethods()
        self.prob = om.Problem()

        aero_builder = AeroBuilderNoCoupling()
        struct_builder = StructBuilderNoCoupling()
        ldxfer_builder = LDXferBuilder(aero_builder, struct_builder)

        aero_builder.initialize(MPI.COMM_WORLD)
        struct_builder.initialize(MPI.COMM_WORLD)
        ldxfer_builder.initialize(MPI.COMM_WORLD)

        self.prob.model.add_subsystem(
            "aero_mesh", aero_builder.get_mesh_coordinate_subsystem()
        )
        self.prob.model.add_subsystem(
            "struct_mesh", struct_builder.get_mesh_coordinate_subsystem()
        )
        self.prob.model.add_subsystem(
            "scenario",
            ScenarioAeroStructural(
                aero_builder=aero_builder,
                struct_builder=struct_builder,
                ldxfer_builder=ldxfer_builder,
                coupling_group_type=None,
            ),
        )
        self.prob.model.connect(
            f"aero_mesh.{MPhysVariables.Aerodynamics.Surface.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Aerodynamics.Surface.COORDINATES_INITIAL}",
        )
        self.prob.model.connect(
            f"aero_mesh.{MPhysVariables.Aerodynamics.Surface.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Aerodynamics.Surface.COORDINATES}",
        )

        self.prob.model.connect(
            f"struct_mesh.{MPhysVariables.Structures.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Structures.COORDINATES}",
        )
        self.prob.setup()

    def test_run_model(self):
        self.common.test_run_model(self)

    def test_scenario_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.aero_pre, AeroPreCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_pre, StructPreCouplingComp
        )
        self.assertIsInstance(
            self.prob.model.scenario.aero_post, AeroPostCouplingCompForNoCoupling
        )
        self.assertIsInstance(
            self.prob.model.scenario.struct_post, StructPostCouplingCompForNoCoupling
        )

    def test_scenario_subsystem_order(self):
        expected_order = ["aero_pre", "struct_pre", "aero_post", "struct_post"]
        self.common.test_subsystem_order(self, self.prob.model.scenario, expected_order)

    def test_no_autoivcs(self):
        self.common.test_no_autoivcs(self)


class TestScenarioAeroStructuralChangeOrderPreAndPostCoupling(unittest.TestCase):
    def setUp(self):
        self.common = CommonMethods()
        self.prob = om.Problem()

        aero_builder = AeroBuilder()
        struct_builder = StructBuilder()
        ldxfer_builder = LDXferBuilder(aero_builder, struct_builder)
        self.pre_coupling_order = ["ldxfer", "struct", "aero"]
        self.post_coupling_order = ["struct", "aero", "ldxfer"]

        aero_builder.initialize(MPI.COMM_WORLD)
        struct_builder.initialize(MPI.COMM_WORLD)
        ldxfer_builder.initialize(MPI.COMM_WORLD)

        self.prob.model.add_subsystem(
            "aero_mesh", aero_builder.get_mesh_coordinate_subsystem()
        )
        self.prob.model.add_subsystem(
            "struct_mesh", struct_builder.get_mesh_coordinate_subsystem()
        )
        self.prob.model.add_subsystem(
            "scenario",
            ScenarioAeroStructural(
                aero_builder=aero_builder,
                struct_builder=struct_builder,
                ldxfer_builder=ldxfer_builder,
                pre_coupling_order=self.post_coupling_order,
                post_coupling_order=self.post_coupling_order,
            ),
        )
        self.prob.model.connect(
            f"aero_mesh.{MPhysVariables.Aerodynamics.Surface.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Aerodynamics.Surface.COORDINATES_INITIAL}",
        )
        self.prob.model.connect(
            f"struct_mesh.{MPhysVariables.Structures.Mesh.COORDINATES}",
            f"scenario.{MPhysVariables.Structures.COORDINATES}",
        )
        self.prob.setup()

    def test_run_model(self):
        self.common.test_run_model(self)

    def test_scenario_components_were_added(self):
        self.assertIsInstance(self.prob.model.scenario.aero_pre, AeroPreCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_pre, StructPreCouplingComp
        )
        self.assertIsInstance(self.prob.model.scenario.coupling, CouplingAeroStructural)
        self.assertIsInstance(self.prob.model.scenario.aero_post, AeroPostCouplingComp)
        self.assertIsInstance(
            self.prob.model.scenario.struct_post, StructPostCouplingComp
        )

    def test_scenario_subsystem_order(self):
        expected_order = [
            "struct_pre",
            "aero_pre",
            "coupling",
            "struct_post",
            "aero_post",
        ]
        self.common.test_subsystem_order(self, self.prob.model.scenario, expected_order)

    def test_invalid_subsystem_order_spelling(self):
        bad_spelling = ["struct", "aero", "xfer"]
        with self.assertRaises(ValueError):
            self.prob.model.scenario._mphys_check_coupling_order_inputs(bad_spelling)

    def test_subsystem_order_too_long(self):
        too_long = ["struct", "aero", "ldxfer", "aero"]
        with self.assertRaises(ValueError):
            self.prob.model.scenario._mphys_check_coupling_order_inputs(too_long)

    def test_no_autoivcs(self):
        self.common.test_no_autoivcs(self)


if __name__ == "__main__":
    unittest.main()
