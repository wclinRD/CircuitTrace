module decode_unit (
    input wire [31:0] inst,
    output wire [31:0] imm,
    output wire [4:0] rs1,
    output wire [4:0] rs2,
    output wire [4:0] rd,
    output wire [3:0] alu_op
);
    assign rd = inst[11:7];
    assign rs1 = inst[19:15];
    assign rs2 = inst[24:20];
    assign imm = { {20{inst[31]}}, inst[31:20] };
    
    assign alu_op = inst[6:3];
endmodule
