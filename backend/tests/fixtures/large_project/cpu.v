module cpu(
    input clk,
    input rst,
    input [31:0] instr,
    output [31:0] alu_out
);

wire [31:0] op_a;
wire [31:0] op_b;
wire [3:0]  alu_op;

decode u_decode (
    .instr(instr),
    .op_a(op_a),
    .op_b(op_b),
    .alu_op(alu_op)
);

alu u_alu (
    .clk(clk),
    .rst(rst),
    .op_a(op_a),
    .op_b(op_b),
    .alu_op(alu_op),
    .result(alu_out)
);

endmodule
