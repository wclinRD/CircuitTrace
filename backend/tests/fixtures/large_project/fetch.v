module fetch_unit (
    input wire clk,
    input wire rst_n,
    input wire branch_taken,
    input wire [31:0] branch_target,
    output reg [31:0] pc
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= 32'h0000_0000;
        end else if (branch_taken) begin
            pc <= branch_target;
        end else begin
            pc <= pc + 4;
        end
    end
endmodule
