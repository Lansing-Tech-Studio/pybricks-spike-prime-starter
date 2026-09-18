# check_project.py
#
# This runs on your computer, not the hub.
#
# It is a friendly pre-flight check for your team's Pybricks project. Run it on
# your computer with:
#
#     python3 check_project.py
#
# It looks over the project the same way a coach would before a competition:
#   1. Every .py file still compiles (block files count too - line 1 is a comment).
#   2. menu_config.py is shaped the way the menu loader expects.
#   3. .pybricks-git.json (the file the Git extension reads) is valid.
#   4. Any robot-setup block files follow the "setup only" rules.
#
# It prints "OK: ..." for things that pass and "PROBLEM: ..." for things that
# need fixing, then a one-line summary. It exits 0 when everything is good and
# a non-zero code when there is at least one PROBLEM, so it also works in CI.
#
# It is desktop-only Python (CPython 3.8+). It uses the `ast` and `json`
# modules from the standard library, which the hub's MicroPython does not have,
# so it refuses to run there instead of crashing with a confusing error.

import sys

# --- Desktop-only guard ------------------------------------------------------
# On the LEGO hub this is MicroPython, which has no `ast` module. Fail fast with
# a message a kid can understand rather than a traceback.
_impl = getattr(sys, "implementation", None)
_impl_name = getattr(_impl, "name", "") if _impl is not None else ""
if _impl_name == "micropython":
    print("PROBLEM: check_project.py runs on your computer, not the hub.")
    print("         Open a terminal on your laptop and run: python3 check_project.py")
    sys.exit(2)

import ast
import glob
import json
import os

# The directory this script lives in is the project root we check.
ROOT = os.path.dirname(os.path.abspath(__file__))

# Collected messages. Every problem makes the script exit non-zero. Warnings are
# printed but do not fail the run (per the contract: unknown menu keys, etc.).
problems = []
warnings = []


def ok(message):
    print("OK: " + message)


def problem(message):
    problems.append(message)
    print("PROBLEM: " + message)


def warn(message):
    warnings.append(message)
    print("NOTE: " + message)


def notice(message):
    # Purely informational - not a problem, not really a warning either.
    print("INFO: " + message)


def repo_path(name):
    return os.path.join(ROOT, name)


def exists(name):
    return os.path.isfile(repo_path(name))


def read_text(name):
    with open(repo_path(name), "r", encoding="utf-8") as handle:
        return handle.read()


# --- Check 1: every .py file compiles ---------------------------------------

def check_compiles():
    py_files = sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "*.py"))
    )
    if not py_files:
        warn("No .py files found in the project root - is this the right folder?")
        return
    any_failed = False
    for name in py_files:
        try:
            source = read_text(name)
            compile(source, name, "exec")
        except SyntaxError as err:
            any_failed = True
            line = err.lineno if err.lineno is not None else "?"
            problem("%s does not compile (line %s): %s" % (name, line, err.msg))
        except OSError as err:
            any_failed = True
            problem("could not read %s: %s" % (name, err))
    if not any_failed:
        ok("all %d Python files compile" % len(py_files))


# --- Check 2: menu_config.py -------------------------------------------------

def _describe_body_statement(node):
    return type(node).__name__


def _is_bundle_hints_assign(node):
    """Is this the `_BUNDLE_HINTS = False` line the bundle-hint block needs?"""
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "_BUNDLE_HINTS"
    )


def _is_bundle_hints_if(node):
    """Is this the `if _BUNDLE_HINTS:` block that lists the import hints?"""
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "_BUNDLE_HINTS"
    )


def _strip_bundle_hints(body):
    """Drop the bundle-hint block from the top of menu_config.py's body.

    The block looks like this, and exists so the uploader sees a real
    `import` line for every mission module (it never actually runs):

        _BUNDLE_HINTS = False
        if _BUNDLE_HINTS:
            import mission_01_go_out_and_turn

    Returns the remaining statements, or None if the block is malformed
    (a problem has already been reported in that case).
    """
    saw_assign = False

    if body and _is_bundle_hints_assign(body[0]):
        if not isinstance(body[0].value, ast.Constant):
            problem(
                "menu_config.py's _BUNDLE_HINTS must be set to a plain "
                "False (it is only there to switch the import hints off)."
            )
            return None
        saw_assign = True
        body = body[1:]

    if body and _is_bundle_hints_if(body[0]):
        if not saw_assign:
            problem(
                "menu_config.py has an `if _BUNDLE_HINTS:` block but never "
                "sets _BUNDLE_HINTS = False above it, so importing the file "
                "would fail. Add that line back."
            )
            return None
        if body[0].orelse:
            problem(
                "menu_config.py's `if _BUNDLE_HINTS:` block must not have an "
                "else - it should only hold `import` lines."
            )
            return None
        for stmt in body[0].body:
            if not isinstance(stmt, ast.Import):
                problem(
                    "menu_config.py's `if _BUNDLE_HINTS:` block may only "
                    "contain plain `import <module>` lines, but it has a %s "
                    "statement." % _describe_body_statement(stmt)
                )
                return None
        body = body[1:]

    return body


def _menu_items_node(module):
    """Return (assign_node, value_node) for the single MENU_ITEMS assignment,
    or (None, None) with problems already reported for anything unexpected."""
    body = list(module.body)

    # An optional leading docstring is allowed and ignored.
    if body and isinstance(body[0], ast.Expr) and isinstance(
        getattr(body[0], "value", None), ast.Constant
    ) and isinstance(body[0].value.value, str):
        body = body[1:]

    # The optional bundle-hint block is allowed too, and ignored.
    body = _strip_bundle_hints(body)
    if body is None:
        return None, None

    if len(body) != 1:
        problem(
            "menu_config.py must contain exactly one statement: "
            "MENU_ITEMS = [ ... ] (optionally preceded by a docstring and "
            "the _BUNDLE_HINTS import block). "
            "Found %d top-level statements." % len(body)
        )
        return None, None

    stmt = body[0]
    target_name = None
    value_node = None
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(
        stmt.targets[0], ast.Name
    ):
        target_name = stmt.targets[0].id
        value_node = stmt.value
    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        # e.g. MENU_ITEMS: list = [...]
        target_name = stmt.target.id
        value_node = stmt.value
    else:
        problem(
            "menu_config.py's only statement must be a MENU_ITEMS assignment, "
            "but found a %s statement instead." % _describe_body_statement(stmt)
        )
        return None, None

    if target_name != "MENU_ITEMS":
        problem(
            "menu_config.py must assign MENU_ITEMS, but it assigns %r instead."
            % target_name
        )
        return None, None

    if value_node is None:
        problem("menu_config.py's MENU_ITEMS has no value.")
        return None, None

    return stmt, value_node


_KNOWN_ITEM_KEYS = {"display", "module", "function", "blocks", "enabled"}


def _valid_display(value):
    if isinstance(value, bool):
        # bool is a subclass of int - reject it as a display number.
        return False
    if isinstance(value, int):
        return 0 <= value <= 99
    if isinstance(value, str):
        return len(value) == 1
    if isinstance(value, list):
        return len(value) == 5 and all(isinstance(row, str) for row in value)
    return False


def _valid_module_name(value):
    return (
        isinstance(value, str)
        and "." not in value
        and value.isidentifier()
    )


def check_menu_config():
    name = "menu_config.py"
    if not exists(name):
        problem("%s is missing." % name)
        return None

    try:
        source = read_text(name)
    except OSError as err:
        problem("could not read %s: %s" % (name, err))
        return None

    try:
        module = ast.parse(source, filename=name)
    except SyntaxError as err:
        problem("%s could not be parsed: %s" % (name, err.msg))
        return None

    _assign, value_node = _menu_items_node(module)
    if value_node is None:
        return None

    try:
        items = ast.literal_eval(value_node)
    except (ValueError, SyntaxError) as err:
        problem(
            "menu_config.py's MENU_ITEMS must be a plain literal list "
            "(only numbers, strings, True/False/None and lists). Problem: %s"
            % err
        )
        return None

    if not isinstance(items, list):
        problem("menu_config.py's MENU_ITEMS must be a list.")
        return None

    referenced_modules = set()
    item_problems = False

    for index, item in enumerate(items):
        where = "MENU_ITEMS[%d]" % index
        if not isinstance(item, dict):
            problem("%s must be a dict, but it is a %s." % (where, type(item).__name__))
            item_problems = True
            continue

        # display (required)
        if "display" not in item:
            problem("%s is missing the required 'display' key." % where)
            item_problems = True
        elif not _valid_display(item["display"]):
            problem(
                "%s has an invalid 'display' (%r). It must be an int 0-99, a "
                "single character, or a list of exactly 5 strings."
                % (where, item["display"])
            )
            item_problems = True

        # module (required)
        if "module" not in item:
            problem("%s is missing the required 'module' key." % where)
            item_problems = True
        elif not _valid_module_name(item["module"]):
            problem(
                "%s has an invalid 'module' (%r). It must be a bare module "
                "name (no dots, a valid Python name)." % (where, item["module"])
            )
            item_problems = True
        else:
            referenced_modules.add(item["module"])

        # function (optional): str or None
        if "function" in item and item["function"] is not None and not isinstance(
            item["function"], str
        ):
            problem(
                "%s has an invalid 'function' (%r). It must be a string or None."
                % (where, item["function"])
            )
            item_problems = True

        # blocks (optional): bool
        if "blocks" in item and not isinstance(item["blocks"], bool):
            problem(
                "%s has an invalid 'blocks' (%r). It must be True or False."
                % (where, item["blocks"])
            )
            item_problems = True

        # enabled (optional): bool
        if "enabled" in item and not isinstance(item["enabled"], bool):
            problem(
                "%s has an invalid 'enabled' (%r). It must be True or False."
                % (where, item["enabled"])
            )
            item_problems = True

        # Unknown keys are a warning, not a failure (the loader ignores them).
        extra = set(item.keys()) - _KNOWN_ITEM_KEYS
        if extra:
            warn(
                "%s has unknown key(s) %s - the menu loader will ignore them."
                % (where, ", ".join(sorted(extra)))
            )

    # Every referenced module must have a matching <module>.py file.
    for mod in sorted(referenced_modules):
        if not exists(mod + ".py"):
            problem(
                "menu_config.py references module %r but %s.py does not exist."
                % (mod, mod)
            )
            item_problems = True

    if not item_problems:
        ok("menu_config.py looks good (%d menu item(s))." % len(items))

    return items


# --- Check 3: .pybricks-git.json --------------------------------------------

_MANIFEST_REQUIRED_KEYS = ("menuConfig", "setupTemplate", "teamSetup", "protected")


def check_manifest():
    name = ".pybricks-git.json"
    if not exists(name):
        problem("%s is missing." % name)
        return None

    try:
        raw = read_text(name)
    except OSError as err:
        problem("could not read %s: %s" % (name, err))
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as err:
        problem("%s is not valid JSON: %s" % (name, err))
        return None

    if not isinstance(data, dict):
        problem("%s must be a JSON object." % name)
        return None

    manifest_ok = True

    if data.get("schemaVersion") != 1:
        problem(
            "%s must have \"schemaVersion\": 1 (found %r)."
            % (name, data.get("schemaVersion"))
        )
        manifest_ok = False

    for key in _MANIFEST_REQUIRED_KEYS:
        if key not in data:
            problem("%s is missing the required key %r." % (name, key))
            manifest_ok = False

    # The setup files (setupTemplate / teamSetup) are allowed to not exist yet -
    # they get authored later in code.pybricks.com. When one of them also
    # appears in "protected" (robot_setup_template.py does), its absence is a
    # notice, not a failure - otherwise the project could never pass this check
    # before the template is authored in the IDE.
    soft_names = set()
    noticed_missing = set()
    for soft_key in ("setupTemplate", "teamSetup"):
        value = data.get(soft_key)
        if isinstance(value, str):
            soft_names.add(value)

    # protected: list of strings, and every entry must exist on disk (except the
    # soft setup-file names above).
    protected = data.get("protected")
    if protected is not None:
        if not isinstance(protected, list) or not all(
            isinstance(p, str) for p in protected
        ):
            problem("%s: \"protected\" must be a list of strings." % name)
            manifest_ok = False
        else:
            for entry in protected:
                if exists(entry):
                    continue
                if entry in soft_names:
                    notice(
                        "%s lists protected file %r which isn't present yet - "
                        "that's OK, it gets authored later in code.pybricks.com."
                        % (name, entry)
                    )
                    noticed_missing.add(entry)
                    continue
                problem(
                    "%s lists protected file %r but it does not exist."
                    % (name, entry)
                )
                manifest_ok = False

    # menuConfig: filename must exist.
    menu_config = data.get("menuConfig")
    if isinstance(menu_config, str):
        if not exists(menu_config):
            problem(
                "%s points menuConfig at %r but it does not exist."
                % (name, menu_config)
            )
            manifest_ok = False
    elif "menuConfig" in data:
        problem("%s: \"menuConfig\" must be a filename string." % name)
        manifest_ok = False

    # setupTemplate / teamSetup: may not exist yet - inform, don't fail.
    setup_files = []
    for soft_key in ("setupTemplate", "teamSetup"):
        value = data.get(soft_key)
        if isinstance(value, str):
            if exists(value):
                setup_files.append(value)
            elif value not in noticed_missing:
                notice(
                    "%s: %s file %r is not present yet - that's OK, it gets "
                    "authored later in code.pybricks.com." % (name, soft_key, value)
                )
        elif soft_key in data:
            problem("%s: \"%s\" must be a filename string." % (name, soft_key))
            manifest_ok = False

    if manifest_ok:
        ok(".pybricks-git.json is valid.")

    return setup_files


# --- Check 4: setup block files ---------------------------------------------

_BLOCKS_PREFIX = "# pybricks blocks file:"


def _find_block_type(node, wanted):
    """Recursively search parsed workspace JSON for a block whose type == wanted."""
    if isinstance(node, dict):
        if node.get("type") == wanted:
            return True
        return any(_find_block_type(v, wanted) for v in node.values())
    if isinstance(node, list):
        return any(_find_block_type(v, wanted) for v in node)
    return False


def check_setup_file(name):
    try:
        source = read_text(name)
    except OSError as err:
        problem("could not read setup file %s: %s" % (name, err))
        return

    lines = source.split("\n")
    first_line = lines[0] if lines else ""

    if not first_line.startswith(_BLOCKS_PREFIX):
        problem(
            "%s is listed as a setup block file but its first line does not "
            "start with '%s'." % (name, _BLOCKS_PREFIX)
        )
        return

    json_text = first_line[len(_BLOCKS_PREFIX):]
    try:
        workspace = json.loads(json_text)
    except json.JSONDecodeError as err:
        problem("%s: the block JSON on line 1 is not valid JSON: %s" % (name, err))
        return

    if not _find_block_type(workspace, "blockGlobalSetup"):
        problem(
            "%s: setup files must contain a 'blockGlobalSetup' block, but "
            "none was found in the workspace JSON." % name
        )

    # The generated Python (everything after line 1) must be setup-only: no
    # run_task( calls.
    python_body = "\n".join(lines[1:])
    if "run_task(" in python_body:
        problem(
            "%s: setup files must not call run_task() - they only define the "
            "robot's setup, they don't run a program." % name
        )


def check_setup_files(setup_files):
    if not setup_files:
        notice("No setup block files present yet - nothing to check.")
        return
    before = len(problems)
    for name in setup_files:
        check_setup_file(name)
    if len(problems) == before:
        ok("setup block file(s) follow the setup-only rules: %s" % ", ".join(setup_files))


# --- Main --------------------------------------------------------------------

def main():
    print("Checking project in: %s" % ROOT)
    print("")

    check_compiles()
    check_menu_config()
    setup_files = check_manifest()
    check_setup_files(setup_files or [])

    print("")
    if problems:
        print(
            "SUMMARY: %d problem(s) found%s. Please fix the PROBLEM lines above."
            % (len(problems), " and %d note(s)" % len(warnings) if warnings else "")
        )
        return 1

    if warnings:
        print(
            "SUMMARY: all checks passed with %d note(s) - see NOTE lines above."
            % len(warnings)
        )
    else:
        print("SUMMARY: all checks passed. Your project looks good!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
