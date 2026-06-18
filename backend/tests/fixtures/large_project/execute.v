module execute_unit (
    input wire [31:0] rs1_data,
    input wire [31:0] rs2_data,
    input wire [3:0] alu_op,
    output reg [31:0] alu_result,
    output reg branch_taken
);
    always @(*) begin
        case (alu_op)
            4'b0000: alu_result = rs1_data + rs2_data;
            4'b0001: alu_result = rs1_data - rs2_data;
            4'b0010: alu_result = rs1_data & rs2_data;
            4'b0011: alu_result = rs1_data | rs2_data;
            4'b0100: alu_result = rs1_data ^ rs2_data;
            default: alu_result = 32'h0;
        endcase
        
        branch_taken = (alu_op == 4'b1000) && (rs1_data == rs2_data);
    end
endmodule
