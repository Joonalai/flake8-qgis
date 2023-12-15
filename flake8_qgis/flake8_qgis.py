# Core Library modules
import ast
import sys
from typing import Any, List, Optional, Tuple

CLASS_FACTORY = "classFactory"

QGIS_INTERFACE = "QgisInterface"

if sys.version_info < (3, 8):
    # Third party modules
    import importlib_metadata
else:
    # Core Library modules
    import importlib.metadata as importlib_metadata

QGS101_AND_QGS103 = (
    "{code} Use 'from {correct_module} import {members}' "
    "instead of 'from {module} import {members}'"
)
QGS102_AND_QGS104 = "{code} Use 'import {correct}' instead of 'import {incorrect}'"
QGS105 = (
    "QGS105 Do not pass iface (QgisInterface) as an argument, "
    "instead import it: 'from qgis.utils import iface'"
)
QGS106 = "QGS106 Use 'from osgeo import {members}' instead of 'import {members}'"


pyqgis_methods = [
    (QgsProject.instance().addMapLayer, None),
    (QgsProject.instance().write, bool),
    (QgsVectorLayer.dataProvider().addFeatures, bool),
    (QgsVectorLayer.startEditing, bool),
    (QgsVectorLayer.commitChanges, bool),
    (QgsVectorLayer.rollBack, bool),
    (QgsVectorLayer.startEditing, bool),
    (QgsVectorLayer.updateExtents, bool),
    (QgsVectorLayer.addFeature, bool),
    (QgsVectorLayer.addFeatures, bool),
    (QgsVectorLayer.deleteFeature, bool),
    (QgsVectorLayer.deleteFeatures, bool),
    (QgsVectorLayer.beginEditCommand, bool),
    (QgsVectorLayer.endEditCommand, bool),
    (QgsVectorLayer.addAttribute, bool),
    (QgsVectorLayer.updateFeature, bool),
    (QgsVectorLayer.deleteAttribute, bool),
    (QgsVectorLayer.addAttributeAlias, bool),
    (QgsVectorLayer.deleteAttributeAlias, bool),
    (QgsVectorLayer.dataProvider().changeAttributeValues, bool),
    (QgsVectorLayer.dataProvider().changeGeometryValues, bool),
    ("QgsVectorLayer.renameAttribute", bool),
    ("QgsVectorLayer.setCustomProperty", bool),
    ("QgsFeature.setAttribute", bool),
    ("QgsGeometry.simplify", QgsGeometry()), # Empty
    ("QgsGeometry.transform", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.translate", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.addPart", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.addPartGeometry", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.addPoints", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.addPointsXY", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.addRing", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.reshapeGeometry", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.rotate", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.splitGeometry", tuple[Qgis.GeometryOperationResult, Any]), # Error or not?
    ("QgsGeometry.addRing", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.addRing", Qgis.GeometryOperationResult), # Error or not?
    ("QgsGeometry.addRing", Qgis.GeometryOperationResult), # Error or not?


]



def _get_qgs101_and_103(
    node: ast.ImportFrom, code: str, package: str, correct_package: Optional[str] = None
) -> List[Tuple[int, int, str]]:
    errors: List[Tuple[int, int, str]] = []
    if node.module is None or not node.module.startswith(package):
        return errors
    errors.append(
        (
            node.lineno,
            node.col_offset,
            QGS101_AND_QGS103.format(
                code=code,
                module=node.module,
                correct_module=node.module.replace("._", ".")
                if correct_package is None
                else node.module.replace(package, correct_package),
                members=", ".join([alias.name for alias in node.names]),
            ),
        )
    )
    return errors


def _get_qgs102_and_qgs104(
    node: ast.Import, code: str, package: str, correct_package: Optional[str] = None
) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where access to a protected member of a class qgs is imported.
    eg. 'import qgs._core...' or 'import qgs._qui...'
    """
    errors: List[Tuple[int, int, str]] = []
    for alias in node.names:
        if alias.name.startswith(package):
            errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    QGS102_AND_QGS104.format(
                        code=code,
                        correct=alias.name.replace("._", ".")
                        if correct_package is None
                        else alias.name.replace(package, correct_package),
                        incorrect=alias.name,
                    ),
                )
            )
    return errors


def _get_qgs101(node: ast.ImportFrom) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where access to a protected member of a class qgs is imported.
    eg. 'from qgs._core import ...' or 'from qgs._qui import ...'
    """
    return _get_qgs101_and_103(node, "QGS101", "qgs._") + _get_qgs101_and_103(
        node, "QGS101", "qgis._"
    )


def _get_qgs102(node: ast.Import) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where access to a protected member of a class qgs is imported.
    eg. 'import qgs._core...' or 'import qgs._qui...'
    """
    return _get_qgs102_and_qgs104(node, "QGS102", "qgs._") + _get_qgs102_and_qgs104(
        node, "QGS102", "qgis._"
    )


def _get_qgs103(node: ast.ImportFrom) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where PyQt is directly imported.
    """
    errors: List[Tuple[int, int, str]] = []
    for qt_version_num in (4, 5, 6):
        errors += _get_qgs101_and_103(
            node, "QGS103", f"PyQt{qt_version_num}", "qgis.PyQt"
        )
    return errors


def _get_qgs104(node: ast.Import) -> List[Tuple[int, int, str]]:
    """
    Get a list of calls where PyQt is directly imported.
    """
    errors: List[Tuple[int, int, str]] = []
    for qt_version_num in (4, 5, 6):
        errors += _get_qgs102_and_qgs104(
            node, "QGS104", f"PyQt{qt_version_num}", "qgis.PyQt"
        )
    return errors


def _get_qgs105(node: ast.FunctionDef) -> List[Tuple[int, int, str]]:
    errors: List[Tuple[int, int, str]] = []
    if node.name == CLASS_FACTORY:
        return errors
    for arg in node.args.args:
        if (
            arg.arg == "iface"
            or (hasattr(arg, "type_comment") and arg.type_comment == QGIS_INTERFACE)
            or (
                arg.annotation
                and hasattr(arg.annotation, "id")
                and arg.annotation.id == QGIS_INTERFACE
            )
        ):
            errors.append((node.lineno, node.col_offset, QGS105))
    return errors


def _get_qgs106(node: ast.Import) -> List[Tuple[int, int, str]]:
    errors: List[Tuple[int, int, str]] = []
    for alias in node.names:
        if alias.name in ("gdal", "ogr"):
            errors.append(
                (
                    node.lineno,
                    node.col_offset,
                    QGS106.format(members=alias.name),
                )
            )
    return errors

def _get_qgs2(node :ast.Call):
    errors: List[Tuple[int, int, str]] = []
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        # Check if the function call is one of the specified PyQGIS methods
        for method, expected_return in pyqgis_methods:
            if func.attr == method.split('.')[1]:
                pass
                # TODO: vaikeaa voi olla katsoa se Attributen id koska se tuskin on luokan nimi...
def check_qgs_methods_with_returns(physical_checker, node):
    if isinstance(node, ast.Expr):
        # Extract method call expressions
        call_expr = node.value
        if isinstance(call_expr, ast.Call):
            func = call_expr.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                # Check if the function call is one of the specified PyQGIS methods
                for method, expected_return in pyqgis_methods:
                    if (
                            func.value.id == method.split('.')[0] and
                            func.attr == method.split('.')[1]
                    ):
                        return_type = expected_return

                        if return_type == 'bool':
                            # Check if the return value is checked with a comparison
                            if not any(isinstance(expr, ast.Compare) and expr.left == node for expr in ast.walk(physical_checker.tree)):
                                physical_checker.add_error(f"QGS001 '{method}' return value not checked with a comparison.", node)
                        elif return_type != 'None':
                            physical_checker.add_error(f"QGS002 '{method}' return value is expected to be of type {return_type}.", node)




class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: List[Tuple[int, int, str]] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:  # noqa N802
        self.errors += _get_qgs101(node)
        self.errors += _get_qgs103(node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> Any:  # noqa N802
        self.errors += _get_qgs102(node)
        self.errors += _get_qgs104(node)
        self.errors += _get_qgs106(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:  # noqa N802
        self.errors += _get_qgs105(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:  # noqa N802
        self.errors += _get_qgs2(node)
        self.generic_visit(node)


class Plugin:
    name = __name__
    version = importlib_metadata.version("flake8_qgis")

    def __init__(self, tree: ast.AST) -> None:
        self._tree = tree

    def run(self):  # noqa
        visitor = Visitor()

        # Add parent
        for node in ast.walk(self._tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node  # type: ignore
        visitor.visit(self._tree)

        for line, col, msg in visitor.errors:
            yield line, col, msg, type(self)
