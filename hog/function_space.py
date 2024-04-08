# HyTeG Operator Generator
# Copyright (C) 2024  HyTeG Team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pyclbr import Function
from typing import Any, List, Optional, Protocol
import sympy as sp

from hog.element_geometry import ElementGeometry, TriangleElement, TetrahedronElement
from hog.exception import HOGException
from hog.math_helpers import grad
from hog.symbolizer import Symbolizer


class FunctionSpace(Protocol):
    """Representation of a finite element function space."""

    @property
    def family(self) -> str:
        """The common name of this FEM space."""
        ...

    @property
    def is_vectorial(self) -> bool:
        """Whether shape functions are scalar or vector valued."""
        ...

    @property
    def is_continuous(self) -> bool:
        """Whether functions in this space are continuous across elements."""
        ...

    @property
    def degree(self) -> int:
        """The polynomial degree of the shape functions."""
        ...

    @property
    def symbolizer(self) -> Symbolizer:
        """The symbolizer used to construct this object."""
        ...

    def shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.Expr]:
        """The basis functions of this FEM space."""
        ...

    def grad_shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.MatrixBase]:
        """Returns a list containing the gradients of the shape functions on the element.

        :param dof_map: this list can be used to specify (remap) the DoF ordering of the element
        """
        if domain in ["ref", "reference"]:
            symbols = self.symbolizer.ref_coords_as_list(geometry.dimensions)
            basis_functions_gradients = [
                grad(f, symbols)
                for f in self.shape(geometry, domain=domain, dof_map=dof_map)
            ]
            return basis_functions_gradients

        raise HOGException(
            f"Gradient of shape function not available for domain type {domain}"
        )

    def num_dofs(self, geometry: ElementGeometry) -> int:
        """The number of DoFs per element."""
        return len(self.shape(geometry))


class LagrangianFunctionSpace(FunctionSpace):
    """Representation of a finite element function spaces.

    Instances of this class provide the shape functions on the reference element as sympy expression.
    """

    def __init__(self, degree: int, symbolizer: Symbolizer):
        """Creates a FunctionSpace of Lagrangian family.

        :param degree: the order of the shape functions
        :param symbolizer: a Symbolizer instance
        """
        if degree not in [0, 1, 2]:
            raise HOGException("Only degree 0, 1 and 2 are supported.")

        self._degree = degree
        self._symbolizer = symbolizer

    @property
    def is_vectorial(self) -> bool:
        return False

    @property
    def is_continuous(self) -> bool:
        return True

    @property
    def degree(self) -> int:
        return self._degree

    @property
    def symbolizer(self) -> Symbolizer:
        return self._symbolizer

    @property
    def family(self) -> str:
        return "Lagrange"

    def shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.Expr]:
        """Returns a list containing the shape functions on the element.

        :param dof_map: this list can be used to specify (remap) the DoF ordering of the element
        """
        if domain in ["ref", "reference"]:
            symbols = self.symbolizer.ref_coords_as_list(geometry.dimensions)

            basis_functions = []

            if (
                isinstance(geometry, TriangleElement)
                and self.family in ["Lagrange"]
                and self._degree == 0
            ):
                basis_functions = [sp.sympify(1)]

            elif (
                isinstance(geometry, TriangleElement)
                and self.family in ["Lagrange"]
                and self._degree == 1
            ):
                basis_functions = [
                    1 - symbols[0] - symbols[1],
                    symbols[0],
                    symbols[1],
                ]

            elif (
                isinstance(geometry, TriangleElement)
                and self.family in ["Lagrange"]
                and self._degree == 2
            ):
                x = symbols[0]
                y = symbols[1]
                basis_functions = [
                    2 * x**2 + 4 * x * y - 3 * x + 2 * y**2 - 3 * y + 1,
                    2 * x**2 - x,
                    2 * y**2 - y,
                    4 * x * y,
                    -4 * x * y - 4 * y**2 + 4 * y,
                    -4 * x**2 - 4 * x * y + 4 * x,
                ]

            elif (
                isinstance(geometry, TetrahedronElement)
                and self.family in ["Lagrange"]
                and self._degree == 0
            ):
                basis_functions = [sp.sympify(1)]

            elif (
                isinstance(geometry, TetrahedronElement)
                and self.family in ["Lagrange"]
                and self._degree == 1
            ):
                basis_functions = [
                    1 - symbols[0] - symbols[1] - symbols[2],
                    symbols[0],
                    symbols[1],
                    symbols[2],
                ]

            elif (
                isinstance(geometry, TetrahedronElement)
                and self.family in ["Lagrange"]
                and self._degree == 2
            ):
                xi_1 = symbols[0]
                xi_2 = symbols[1]
                xi_3 = symbols[2]
                basis_functions = [
                    (
                        2.0 * xi_1 * xi_1
                        + 4.0 * xi_1 * xi_2
                        + 4.0 * xi_1 * xi_3
                        - 3.0 * xi_1
                        + 2.0 * xi_2 * xi_2
                        + 4.0 * xi_2 * xi_3
                        - 3.0 * xi_2
                        + 2.0 * xi_3 * xi_3
                        - 3.0 * xi_3
                        + 1.0
                    ),
                    (2.0 * xi_1 * xi_1 - 1.0 * xi_1),
                    (2.0 * xi_2 * xi_2 - 1.0 * xi_2),
                    (2.0 * xi_3 * xi_3 - 1.0 * xi_3),
                    (4.0 * xi_2 * xi_3),
                    (4.0 * xi_1 * xi_3),
                    (4.0 * xi_1 * xi_2),
                    (
                        -4.0 * xi_1 * xi_3
                        - 4.0 * xi_2 * xi_3
                        - 4.0 * xi_3 * xi_3
                        + 4.0 * xi_3
                    ),
                    (
                        -4.0 * xi_1 * xi_2
                        - 4.0 * xi_2 * xi_2
                        - 4.0 * xi_2 * xi_3
                        + 4.0 * xi_2
                    ),
                    (
                        -4.0 * xi_1 * xi_1
                        - 4.0 * xi_1 * xi_2
                        - 4.0 * xi_1 * xi_3
                        + 4.0 * xi_1
                    ),
                ]

            else:
                raise HOGException(
                    "Basis functions not implemented for the specified element type and geometry."
                )

            if dof_map:
                raise HOGException("DoF reordering not implemented.")

            return basis_functions

        raise HOGException(f"Shape function not available for domain type {domain}")

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LagrangianFunctionSpace):
            return False
        return self.family == other.family and self._degree == other._degree

    def __str__(self):
        return f"{self.family}, degree: {self._degree}"

    def __repr__(self):
        return str(self)


class TensorialVectorFunctionSpace(FunctionSpace):
    def __init__(self, component: int, function_space: FunctionSpace):
        self._component_function_space = function_space
        self._component = component

    @property
    def is_vectorial(self) -> bool:
        return True

    @property
    def degree(self) -> int:
        return self._component_function_space.degree

    @property
    def symbolizer(self) -> Symbolizer:
        return self._component_function_space.symbolizer

    @property
    def family(self) -> str:
        return self._component_function_space.family

    @property
    def component(self) -> int:
        return self._component

    @property
    def is_continuous(self) -> bool:
        return self._component_function_space.is_continuous

    def _to_vector(self, phi: sp.Expr, geometry: ElementGeometry) -> sp.MatrixBase:
        dimensions = geometry.dimensions
        return sp.Matrix(
            [
                [phi if c == self._component else sp.sympify(0)]
                for c in range(dimensions)
            ]
        )

    def _to_matrix(self, grad_phi: sp.Expr, geometry: ElementGeometry) -> sp.MatrixBase:
        grad_phi = grad_phi.transpose().tolist()[0]
        dimensions = geometry.dimensions
        zero = [sp.sympify(0) for i in range(dimensions)]
        return sp.Matrix(
            [(grad_phi if c == self._component else zero) for c in range(dimensions)]
        )

    def shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.Expr]:
        shape_functions = self._component_function_space.shape(
            geometry, domain, dof_map
        )
        return [self._to_vector(phi, geometry) for phi in shape_functions]

    def grad_shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.MatrixBase]:
        grad_shape_functions = self._component_function_space.grad_shape(
            geometry, domain, dof_map
        )
        return [
            self._to_matrix(grad_shape, geometry) for grad_shape in grad_shape_functions
        ]

    def num_dofs(self, geometry: ElementGeometry) -> int:
        """Returns the number of DoFs per element."""
        return len(self.shape(geometry))

    def __eq__(self, other: Any) -> bool:
        if type(self) != type(other):
            return False
        if not hasattr(other, "_component_function_space"):
            return False
        if self._component != other._component:
            return False
        return self._component_function_space == other._component_function_space

    def __str__(self):
        return f"Vectorial({self._component_function_space})"

    def __repr__(self):
        return str(self)


class EnrichedGalerkinFunctionSpace(FunctionSpace):
    def __init__(
        self,
        symbolizer: Symbolizer,
    ):
        self._symbolizer = symbolizer
        self._affine = None

    @property
    def family(self) -> str:
        return "EnrichedGalerkin"

    @property
    def is_vectorial(self) -> bool:
        return True

    def init_affine(self, affine):
        self._affine = affine

    @property
    def is_continuous(self) -> bool:
        return False

    @property
    def degree(self) -> int:
        return 1

    @property
    def symbolizer(self) -> Symbolizer:
        return self._symbolizer

    def shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.Expr]:
        if domain not in ["reference", "ref"] or dof_map is not None:
            raise HOGException(
                "Unsupported parameters for EnrichedGalerkinFunctionSpace"
            )
        symbols = self._symbolizer.ref_coords_as_list(geometry.dimensions)
        midpoint = sp.Matrix(
            [
                [sp.Rational(1, geometry.dimensions + 1)]
                for i in range(geometry.dimensions)
            ]
        )
        x = sp.Matrix([[symbols[i]] for i in range(geometry.dimensions)])
        # return [self._affine * (x - midpoint)]
        return [(x - midpoint)]

    def grad_shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.MatrixBase]:
        # return [self._affine]
        return sp.Matrix([[1, 0], [0, 1]])

    def num_dofs(self, geometry: ElementGeometry) -> int:
        """Returns the number of DoFs per element."""
        return len(self.shape(geometry))

    def __str__(self):
        return f"EnrichedDG"

    def __repr__(self):
        return str(self)


class N1E1Space(FunctionSpace):
    """Nedelec edge elements of type I and order 1 for problems in H(curl)."""

    def __init__(self, symbolizer: Symbolizer):
        self._symbolizer = symbolizer

    @property
    def is_vectorial(self) -> bool:
        return True

    @property
    def is_continuous(self) -> bool:
        return False

    @property
    def degree(self) -> int:
        return 1

    @property
    def symbolizer(self) -> Symbolizer:
        return self._symbolizer

    @property
    def family(self) -> str:
        return "N1E1"

    def shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.Expr]:
        if not isinstance(geometry, TetrahedronElement):
            raise HOGException(
                f"N1E1Space is only implemented for tetrahedral elements"
            )

        if domain in ["ref", "reference"]:
            symbols = self.symbolizer.ref_coords_as_list(geometry.dimensions)
            x, y, z = symbols

            basis = [
                sp.Matrix([0, -z, y]),
                sp.Matrix([-z, 0, x]),
                sp.Matrix([-y, x, 0]),
                sp.Matrix([z, z, -x - y + 1]),
                sp.Matrix([y, -x - z + 1, y]),
                sp.Matrix([-y - z + 1, x, x]),
            ]

            if dof_map:
                raise HOGException("DoF reordering not implemented.")

            return basis

        raise HOGException(f"Shape function not available for domain type {domain}")

    def grad_shape(
        self,
        geometry: ElementGeometry,
        domain: str = "reference",
        dof_map: Optional[List[int]] = None,
    ) -> List[sp.MatrixBase]:
        return 6 * [None]

    def __eq__(self, other: Any) -> bool:
        return type(self) == type(other)

    def __str__(self):
        return f"N1E1"

    def __repr__(self):
        return str(self)
