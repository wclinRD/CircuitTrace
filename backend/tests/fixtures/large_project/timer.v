module timer (
    input wire clk,
    input wire rst_n,
    input wire en,
    output reg timeout
);
    reg [31:0] count;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 0;
            timeout <= 0;
        end else if (en) begin
            if (count == 32'hFFFF) begin
                count <= 0;
                timeout <= 1;
            end else begin
                count <= count + 1;
                timeout <= 0;
            end
        end
    end
endmodule
