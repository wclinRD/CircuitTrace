module alu(
    input clk,
    input rst,
    input [31:0] op_a,
    input [31:0] op_b,
    input [3:0] alu_op,
    output reg [31:0] result
);

always @(posedge clk or posedge rst) begin
    if (rst) begin
        result <= 32'b0;
    end else begin
        case (alu_op)
            4'b0000: result <= op_a + op_b;
            4'b0001: result <= op_a - op_b;
            default: result <= 32'b0;
        endcase
    end
end

endmodule
