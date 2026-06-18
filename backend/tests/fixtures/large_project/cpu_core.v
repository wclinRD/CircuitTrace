module cpu_core (
    input wire clk,
    input wire rst_n,
    input wire [31:0] inst,
    input wire [31:0] mem_rdata,
    output wire [31:0] pc,
    output wire [31:0] mem_wdata,
    output wire [31:0] mem_addr,
    output wire mem_we,
    output wire mem_en
);
    wire [31:0] fetch_pc;
    wire [31:0] dec_imm;
    wire [4:0] dec_rs1;
    wire [4:0] dec_rs2;
    wire [4:0] dec_rd;
    wire [3:0] dec_alu_op;
    
    wire [31:0] alu_result;
    wire branch_taken;

    assign pc = fetch_pc;
    assign mem_addr = alu_result;
    assign mem_wdata = 32'h0;
    assign mem_we = 1'b0;
    assign mem_en = 1'b1;

    fetch_unit u_fetch (
        .clk(clk),
        .rst_n(rst_n),
        .branch_taken(branch_taken),
        .branch_target(alu_result),
        .pc(fetch_pc)
    );

    decode_unit u_decode (
        .inst(inst),
        .imm(dec_imm),
        .rs1(dec_rs1),
        .rs2(dec_rs2),
        .rd(dec_rd),
        .alu_op(dec_alu_op)
    );

    execute_unit u_execute (
        .rs1_data(fetch_pc),
        .rs2_data(dec_imm),
        .alu_op(dec_alu_op),
        .alu_result(alu_result),
        .branch_taken(branch_taken)
    );

endmodule
