module decode(
    input [31:0] instr,
    output reg [31:0] op_a,
    output reg [31:0] op_b,
    output reg [3:0] alu_op
);

always @(*) begin
    op_a = instr[15:0];
    op_b = instr[31:16];
    alu_op = instr[3:0];
end

endmodule
