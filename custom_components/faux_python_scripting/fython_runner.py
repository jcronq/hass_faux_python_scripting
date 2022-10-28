from .fython_parser import decompose_script


class FythonRuntimeError(RuntimeError):
    """Runtime Error for Fython execution"""


def evaluate_script(script: str, timezone, global_var=None):
    """Evaluate a config script"""
    word_list = decompose_script(script)
    program = _parse_program(word_list, timezone)
    return _evaluate_program(program, global_var)


def _evaluate_program(prog, global_var=None):
    prog_idx = 0
    exec_stack = []
    while prog_idx < len(prog):
        instr = prog[prog_idx]
        if instr["type"] == "var":
            exec_stack.append(instr["value"])
            prog_idx += 1
        elif instr["type"] == "arithmatic":
            next_node = prog[prog_idx + 1]
            if next_node["type"] == "var":
                var2 = next_node["value"]
            elif next_node["type"] == "func":
                var2 = _evaluate_program([next_node])
            else:
                raise RuntimeError(f"Invalid program node found.  Expecting either func or var, found {next_node}")
            var1 = exec_stack.pop(-1)
            if instr["value"] == "+":
                exec_stack.append(var1 + var2)
            elif instr["value"] == "-":
                exec_stack.append(var1 - var2)
            elif instr["value"] == "/":
                exec_stack.append(var1 / var2)
            elif instr["value"] == "*":
                exec_stack.append(var1 * var2)
            else:
                raise RuntimeException(f'Arithmatic Instruction {instr["value"]} has not been implemented.')
            prog_idx += 2
        elif instr["type"] == "func":
            func = instr["value"]
            args = [_evaluate_program(arg) for arg in instr["args"]]
            exec_stack.append(_run_func(func, args, global_var))
            prog_idx += 1
        else:
            raise RuntimeException(f"Unexpected Instruction of {instr} found at {prog_idx}")
    if len(exec_stack) != 1:
        raise RuntimeException(
            f"Error: exec_stack has {len(exec_stack)} values left at program completion.{exec_stack}"
        )
    return exec_stack.pop(-1)


def _run_func(func_name, args, global_var=None):
    result = None
    if func_name == "min":
        result = min(args)
    elif func_name == "max":
        result = max(args)
    elif func_name == "lookup":
        if len(args) > 1:
            raise RuntimeException(f"Built-in Function 'lookup()' expects only 1 argument, received {args}")
        lookup_path = args[0].split(".")
        lookup_step = global_var
        for path in lookup_path:
            if path not in lookup_step:
                return None
            lookup_step = lookup_step[path]
        result = lookup_step
    else:
        raise RuntimeException(f"Built-in Function {func_name} has not been implemented.")
    return result
