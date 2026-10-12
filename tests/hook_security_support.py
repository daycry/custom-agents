"""Pure shared AST support for the two independent hook security suites."""
import ast


def _sin_docstrings(tree):
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if isinstance(body, list):
            node.body = [statement for statement in body
                         if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
                                 and isinstance(statement.value.value, str))] or [ast.Pass()]
    return tree


def local_urlparse_code(original):
    """Exclude only the local urlparse API with an unshadowed exact import.

    Other urllib uses, aliases, unknown attributes and strings remain visible;
    this never permits the urllib namespace or an entire script by name.
    """
    try:
        tree = ast.parse(original)
    except SyntaxError:
        return original
    tree = _sin_docstrings(tree)
    nodes = list(ast.walk(tree))
    imported = any(isinstance(node, ast.Import) and any(alias.name == 'urllib.parse' and alias.asname is None
                   for alias in node.names) for node in tree.body)
    rebound = any((isinstance(node, ast.Name) and node.id == 'urllib' and isinstance(node.ctx, (ast.Store, ast.Del)))
                  or (isinstance(node, ast.arg) and node.arg == 'urllib') for node in nodes)
    rebound |= any(isinstance(node, (ast.Import, ast.ImportFrom)) and any(alias.asname == 'urllib'
                   or (alias.name == 'urllib' and alias.asname is None) for alias in node.names) for node in nodes)
    if not imported or rebound:
        return original

    class LocalParse(ast.NodeTransformer):
        def visit_Import(self, node):
            node.names = [alias for alias in node.names if not (alias.name == 'urllib.parse' and alias.asname is None)]
            return node if node.names else None

        def visit_Call(self, node):
            self.generic_visit(node)
            function = node.func
            if (isinstance(function, ast.Attribute) and function.attr == 'urlparse'
                    and isinstance(function.value, ast.Attribute) and function.value.attr == 'parse'
                    and isinstance(function.value.value, ast.Name) and function.value.value.id == 'urllib'):
                node.func = ast.copy_location(ast.Name(id='_local_urlparse', ctx=ast.Load()), function)
            return node

    return ast.unparse(ast.fix_missing_locations(LocalParse().visit(tree)))
