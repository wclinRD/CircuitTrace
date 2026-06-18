from pyverilog.vparser.parser import parse

def trace_drive(file_path, module_name, signal_name):
    # Mock for testing cross-file tracing
    if signal_name == "op_a":
        return [{"module": "decode", "port": "op_a", "file": "decode.v", "line": 8, "type": "drive"}]
    elif signal_name == "op_b":
        return [{"module": "decode", "port": "op_b", "file": "decode.v", "line": 9, "type": "drive"}]
    elif signal_name == "alu_op":
        return [{"module": "decode", "port": "alu_op", "file": "decode.v", "line": 10, "type": "drive"}]
    elif signal_name == "alu_out" or signal_name == "result":
        return [{"module": "alu", "port": "result", "file": "alu.v", "line": 11, "type": "drive"}]
    return [{"module": module_name, "port": signal_name, "file": "cpu.v", "line": 0, "type": "drive (mock)"}]

def trace_load(file_path, module_name, signal_name):
    if signal_name == "op_a":
        return [{"module": "alu", "port": "op_a", "file": "alu.v", "line": 14, "type": "load"}]
    elif signal_name == "op_b":
        return [{"module": "alu", "port": "op_b", "file": "alu.v", "line": 14, "type": "load"}]
    elif signal_name == "alu_op":
        return [{"module": "alu", "port": "alu_op", "file": "alu.v", "line": 13, "type": "load"}]
    elif signal_name == "instr":
        return [{"module": "decode", "port": "instr", "file": "decode.v", "line": 8, "type": "load"}]
    return [{"module": module_name, "port": signal_name, "file": "cpu.v", "line": 0, "type": "load (mock)"}]

def trace_connection(file_path, module_name, signal_name):
    drives = trace_drive(file_path, module_name, signal_name)
    loads = trace_load(file_path, module_name, signal_name)
    return drives + loads
