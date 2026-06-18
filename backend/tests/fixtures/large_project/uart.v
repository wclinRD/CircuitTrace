module uart_top (
    input wire pclk,
    input wire presetn,
    input wire [31:0] paddr,
    input wire psel,
    input wire penable,
    input wire pwrite,
    input wire [31:0] pwdata,
    output wire [31:0] prdata,
    output wire pready,
    
    input wire rx,
    output wire tx
);
    assign pready = 1'b1;
    assign prdata = 32'h0;
    assign tx = rx;
endmodule
