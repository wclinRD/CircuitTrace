module memory_ctrl (
    input wire clk,
    input wire rst_n,
    input wire en,
    input wire we,
    input wire [31:0] addr,
    input wire [31:0] wdata,
    output reg [31:0] rdata,
    output reg [31:0] inst_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rdata <= 32'h0;
            inst_out <= 32'h0000_0013;
        end else if (en) begin
            if (we) begin
            end else begin
                rdata <= 32'hDEADBEEF;
                inst_out <= 32'h0000_0013;
            end
        end
    end
endmodule
